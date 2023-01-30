Title: Gossip Network Example
Date: 2023-01-??
Modified:
Category: Programming
Tags: network-programming
Slug: gossip-network
Summary: Walkthrough of a gossip protocol network implementation



<figure>
<img src="images/06-1_social-network.jpeg" style="width:100%;"
alt="representative illustration of a social network">
</figure>



## Context

I was given this interesting take-home assignment while interviewing for a
company last year: implement a simple peer-to-peer network of servers that
communicate with each other using a gossip protocol.

These were their specified requirements:

* The network must support up to 16 individual servers (nodes) running
simultaneously.

* At any given time, each node can only have knowledge of 3 other nodes in the
network.

* At minimum, each node must provide two API methods:

```python
def submit_message(message: str) -> None:
    """Handle an incoming message."""

def get_messages() -> List[str]:
    """Returns a list of all messages since this node started.

    Each message should include the path it followed to reach this node.
    
    Example output:
    - Apple (Node 1 -> Node 8 -> Node 10)
    - Banana (Node 3 -> Node 5 -> Node 10)
    - Orange (Node 7 -> Node 15 -> Node 9 -> Node 10)
    """
```

* A message submitted to a single node should eventually be received by **all
nodes** in the network.

* Nodes can only communicate with each other through network calls (not
in-process function calls). The actual networking protocol is up to you, so
feel free to choose between TCP, UDP, HTTP, etc.

* Your solution must be implemented in Python.

They provided stub classes for the client and the server, and a simple CLI
UI for interacting with the gossip network, so in effect, the design of the
system. So all that remained was for me to color in the boxes, so to speak.

Project repository here: https://github.com/jyscao/dapper-labs-gossip



## Getting Started

Of course, the first order of business was to install the necessary software
for development: Python 3, Docker and Poetry.

After installing the development dependencies (Python 3, Docker & [Poetry](https://python-poetry.org/))
and [fixing an issue](https://github.com/jyscao/dapper-labs-gossip/commit/af3a5a0a0d4de62d1416de58898fb567a420ba43)
with the poetry lockfile that failed to install the Python dependencies, I was
ready to test out the skeleton gossip network using the provided commands:

* `start-network` - spins up a network of 16 nodes using Docker Compose
* `stop-network` - stops all nodes running in the network
* `send-message` - send a message to a node once the network has been started
* `get-messages` - returns all messages received by a single node
* `remove-node` - stops a single node in the network

Unfortunately, I ran into another roadblock here in the form of getting the
nodes running as individual Docker containers to communicate with each other.
Being the Docker (and containers in general) hater that I am, I decided to
[rip out the entire Docker infrastructure and replace it with the simple to use `multiprocessing` module from Python's standard library](https://github.com/jyscao/dapper-labs-gossip/commit/0b7d19acd8519e3282551e13d86365e024632c4f).

Once that was all in place, I was finally ready to start implementing the
client and the server.



## Implementation Details

Let me showcase the components of the gossip network by taking you through,
roughly in sequence, what happens when one executes the `send-message` command
for example, to any given node.


### CLI & Client

The CLI is powered by the [`docopt`](http://docopt.org/) package, and invoked
through Poetry. So when the command `gossip send-message <node-number>
<message>` is executed, `docopt` parses then recognizes that the predefined
command `send-message` has been invoked, thus activating the following
conditional block:

```python
    elif args["send-message"]:
        message = args["<message>"]
        client = init_gossip_client(args["<node-number>"])
        client.send_message(message, relay_limit=int(args["--relays"]))
        print(f"Message sent to {client}")
```

Where `init_gossip_client` initializes and returns an instance of
`GossipClient` to the specified node, upon which the client's `send_message`
method (shown below) is invoked:

```python
    def send_message(self, message, is_relay=False, relay_limit=1):
        """Send a message to the current server."""
        cmd = "/RELAY" if is_relay else "/NEW"
        self._send_to_server(f"{cmd}:{relay_limit}|{message}")
```

The `_send_to_server` "private" method simply opens a TCP socket connection to
its corresponding `GossipServer`'s TCP server that's running on `localhost`
and a port uniquely determined by the `<node-number>`.

In the case of a new message sent to a node, the `cmd` metadata which is
prepended to the entire text streamed to the server, is set to `"/NEW"`.
The `"/RELAY"` `cmd` metadata is used when intermediate nodes pass received
messages to their neighbors.

This pseudo-IRC-command metadata will be discussed in more detail in the
Message Handling subsection of the server implementation below.


### Server

Each node's server `GossipServer` has the single public method `start` that's
called on `start-network`, creating an instance of `GossipTCPServer`, which
inherits from [`socketserver.ThreadingTCPServer`](https://docs.python.org/3/library/socketserver.html#socketserver.ThreadingTCPServer),
thereby giving it the method [`serve_forever`](https://docs.python.org/3/library/socketserver.html#socketserver.BaseServer.serve_forever):

```python
class GossipServer:
    """A server that participates in a peer-to-peer gossip network."""

    def __init__(self, server_address, peer_addrs):
        """Initialize a server with a list of peer addresses.

        Peer addresses are in the form HOSTNAME:PORT.
        """
        hostname, port = server_address.split(":")
        self.host_port_tup = (hostname, int(port))
        self.ss = ServerSettings(hostname, port, peer_addrs)

    def start(self):
        print(f"Starting Gossip-Node-{self.ss.node_id} with peers:".ljust(36) + f" {', '.join(str(p.id) for p in self.ss.peers)}")
        with GossipTCPServer(self.host_port_tup, GossipMessageHandler, self.ss) as server:
            server.serve_forever()
```

#### Server Settings

The class member `ss` above is the `ServerSettings` dataclass shown below,
which essentially holds all the configuration data (`hostname`, `port`,
`node_id`, etc.) and state (`peers`, received messages stored in `msgs_box`)
of each node's server instance:

```python
@dataclass
class ServerSettings:
    hostname:   str
    port:       int
    peer_addrs: list[str]
    node_id:    int = None
    peers:      list[GossipClient] = field(init=False)
    msgs_box:   dict[dict] = field(default_factory=dict)
```

#### Message Handling

Of course, the bulk of the work is done by the `GossipMessageHandler`, which
subclasses [`socketserver.StreamRequestHandler`](https://docs.python.org/3/library/socketserver.html#socketserver.StreamRequestHandler):

```python
class GossipMessageHandler(StreamRequestHandler):

    def handle(self):
        self.cmd, self.msg_data = self.rfile.readline().strip().decode().split(":", maxsplit=1)
        self._get_cmd_handler()()

    def _get_cmd_handler(self):
        return {
            "/NEW":   self._proc_new_msg,
            "/RELAY": self._proc_relayed_msg,
            "/GET":   self._send_client_msgs_data,
            "/PEERS": self._get_peers_info,
            "/REMOVE": self._remove_peer,
        }[self.cmd]

```

As you can see from the definition of `_get_cmd_handler` above,
`GossipMessageHandler` recognizes 5 different types of commands, which are
specified using the aforementioned pseudo-IRC-like command syntax.

When the bytestream from the node's client is recieved and handled by the
server, the data is split into 2 portions: the command and the message data.
In our example of the `"/NEW"` command, the `_proc_new_msg` method is called
to handle it:

```python
    def _proc_new_msg(self):
        self._set_relay_limit_and_msg_text_on_send()
        self.msg_id = f"{self.msg_content}_{time.time_ns()}"
        self.curr_msg_attrs = self.server.ss.msgs_box[self.msg_id] = self._init_new_msg_attrs()
        self.node_path = [self.server.ss.node_id]
        self._save_path_and_relay()
```

First the `msg_data` is parsed to set the `relay_limit` (more on this later),
and the message content. Then the current timestamp is appended to the messge
content to create the unique `msg_id`. Next a metatdata map is initialized for
the current message with `_init_new_msg_attrs`:

```python
    def _init_new_msg_attrs(self):
        return {
            "in_paths":   [],
            "in_counts":  Counter({p.id: 0 for p in self.server.ss.peers}),
            "out_counts": Counter({p.id: 0 for p in self.server.ss.peers}),
            "is_unread":  True,
        }
```

The `"in_paths"` key will come to contain the list of nodes this message has
traversed to reach the current node. The `"in_counts"` & `"out_counts"` are
respectively used to track whether the current node should accept and save
the incoming message, and broadcast it back out to its neighbor nodes, as
determined by the value of `relay_limit`.

Finally the new message is saved into the `ss.msg_box` `dict` of the node, and
relayed onwards to its peers. As implemented here:

```python
    def _save_path_and_relay(self):
        self.curr_msg_attrs["in_paths"].append(self.node_path)
        self._relay_to_peers((self.msg_id, self.node_path))

    def _relay_to_peers(self, data):
        for p in self._get_peers_to_relay():
            if self.curr_msg_attrs["out_counts"][p.id] < self.relay_limit:
                p.send_message(json.dumps(data), is_relay=True, relay_limit=self.relay_limit)
                self.curr_msg_attrs["out_counts"][p.id] += 1

    def _get_peers_to_relay(self):
        if self.cmd == "/NEW":
            return self.server.ss.peers
        elif self.cmd == "/RELAY":
            # filter out the preceeding node which relayed the current message to this node
            return [p for p in self.server.ss.peers if p.id != self.prev_node]
        else:
            raise Exception("this should never be reached!")
```

As you can see, when the message sent to the node is new (command is
`"/NEW"`), the current node will relay the message to all of its neighbors
using their clients (`p.send_message(...)`). But if the message was already
one that has been relayed to it from a previous node, the node will
exclude the upstream relaying node when proceeding with its own relaying
responsibilities.

This is basically how the GossipServer works. For how the other commands are
handled by it, please read the code.


### Network Topology & Peers

You may recall seeing in the `ServerSettings` dataclass shown earlier that
each node's server contained a `peers` property of type `list[GossipClient]`.
It's certainly fair to question exactly how the peers of each node are
assigned, and by extension the network as a whole is constructed. As is often
the case in Python, a mature and robust library exists for one's domain of
interest, which in our case is [NetworkX](https://networkx.org/): a Python
package for the creation, manipulation, and study of the structure, dynamics,
and functions of complex networks.

NetworkX provides [generator functions](https://networkx.org/documentation/stable/reference/generators.html)
for over a hundred types of graphs. It was trivial to use its `cycle_graph`
generator to replace the stub graph generator provided in the original project
specs. Once a basic [undirected `Graph`](https://networkx.org/documentation/stable/reference/classes/graph.html)
object has been created based on the desired parameters (e.g. the number of
nodes), useful operations such as retrieving the neighbors/peers of any given
node is provided out-of-the-box by its API.

<figure>
<img src="images/06-2_circular-network.jpeg" style="width:100%;"
alt="">
</figure>

Along the same vein, generating a random network is also straightforward
by utilizing `random_regular_graph`. In addition to specifying
the number of nodes *n*, we must also pass the degree *d* of each
node, which defaults to 3, as specified in the original problem
requirement. Note that *n×d* must be even, by the [handshaking
lemma](https://en.wikipedia.org/wiki/Handshaking_lemma).

<figure>
<img src="images/06-3_random-network.jpeg" style="width:100%;"
alt="">
</figure>

Adding a new type of network is also quite simple, which I shall demonstrate.

* plotting (give example of extending: https://networkx.org/documentation/stable/reference/generated/networkx.generators.community.caveman_graph.html)





## Considerations

* number of relays -> requires tracking messages by ID
* alternative messaging mechanism -> check if message has already been received by node, if so, skip and just relay
* display delivery paths of messages
* talk about Tribler: https://github.com/Tribler/tribler












## Extras & Additions

### Implemented (briefly mention this, and ask reader to just refer to code)

* list-peers
* only show shortest or longest path taken by message
* set number of nodes & connectedness
* display arrival time of messages

### Potential TODOs

* check TODO.md
