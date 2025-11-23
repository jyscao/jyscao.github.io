Title: Multi-Birthday Problem
Date: 2023-03-
Category: Programming
Tags: python, math, probability
Slug:
Summary:



<figure>
<img src="" style="width:100%;"
alt="">
</figure>



The classical birthday problem asks one to solve for the number of people
needed for the probability of 2 or more random persons sharing the same
birthday to exceed 50%.

In this post I'd like to explore one variant of this more generalized problem:
that is finding the number of people needed for the probability of *N* or more
random persons sharing the same birthday to exceed 50%.

I shall take you through the mathematical derivation for the closed-form
combinatorial solution to this problem. Then code it up in Python, while
progressively enhancing it.


## Theory

The *N* = 2 case of the birthday problem is easily reasoned through using
some straightfoward probability techniques. Specifically by solving for the
complement of the event that we're actually looking for. That is, to find
the probability of 2 or more persons sharing the same birthday in a group of
*P* persons in total, it is easier to calculate the probability that all *P*
persons in the given group have distinct birthdays. Then since the event that
we're looking for is mutually exclusive to the one that we've just calculated,
the final probability can be obtained through a simple subtraction from 1.
