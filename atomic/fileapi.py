#!/usr/bin/env python3
"""
API implementation for using a local file as the data store.
"""
from colorama import Fore, Style
import networkx as nx

from atomic import api, graph, serial, log


class FileAPI:
    """File-system backed implementation of the API."""

    def __init__(self, G=None):
        self.logger = log.get_logger('api')
        self.G = G or graph.load()
        self.Node = FileNodeAPI(self.G, self.logger)
        self.Edge = FileEdgeAPI(self.G, self.logger)

    def save(self):
        graph.save(self.G)


class FileNodeAPI(api.NodeAPISpec):
    """File-system backed implementation of the Node API."""

    def __init__(self, G, logger):
        self.logger = logger
        self.G = G
        # Find the highest valued node
        serial_idx = max(self.G.nodes_iter()) + 1 if len(self.G) > 0 else 0
        self.serial = serial.Serial(serial_idx)

    def get(self, idx=None):
        """Retrieve an item by index (uuid)."""
        if idx is None:
            self.logger.debug("Retrieving all nodes")
            return graph.hierarchy(self.G)
        self.logger.debug("Retrieving node w/ id=%d", idx)
        return self.G.node[idx]

    def add(self, parent=None, **kwargs):
        idx = self.serial.index
        self.logger.debug("Adding node %s", idx)
        self.G.add_node(idx, attr_dict=kwargs)  # Create node
        if parent is not None:
            self.logger.debug("Linking to %s", parent)
            self.G.add_edge(parent, idx, parent_of=True)  # Link to parent
        graph.save(self.G)

    def update(self, idx, **kwargs):
        """Update item attributes."""
        self.G.node[idx] = {**self.G.node[idx], **kwargs}
        graph.save(self.G)

    def delete(self, idx):
        """Remove a node from the graph."""
        try:
            self.G.remove_node(idx)
            graph.save(self.G)
        except nx.exception.NetworkXError:
            return ValueError("{:d} wasn't found in the graph".format(idx))

    def binary_add(self, item):
        """Insert an item after using a binary-search comparison."""
        lo, hi = 0, len(self.items) - 1
        while lo <= hi:
            mid = lo + hi >> 1  # Find the midpoint with bit shifting!
            ans = self.guided_prompt(lo, mid, hi)
            if ans is None:
                return
            if ans:  # User said higher
                hi = mid - 1
            else:  # User said lower
                lo = mid + 1
        item.uid = self.serial.index
        self.items.insert(lo, item)

    def guided_prompt(self, lo, mid, hi):
        print("Bracketing: ({lo}, {mid}, {hi})"
              .format(lo=Fore.RED + 'lo=' + str(lo) + Style.RESET_ALL,
                      mid=Fore.YELLOW + 'mid=' + str(mid) + Style.RESET_ALL,
                      hi=Fore.GREEN + 'hi=' + str(hi) + Style.RESET_ALL))
        ans = None
        higher = ['h', 'k']
        lower = ['l', 'j']
        while not ans:
            print("Higher[{higher}] or Lower[{lower}]: {items}".format(
                higher=','.join(higher), lower=','.join(lower),
                items=self.items[mid]))
            try:
                ans = input()
            except EOFError:
                return None
            if ans in higher:  # User said higher
                return True
            elif ans in lower:  # User said lower
                return False
            else:
                print("I'm sorry, I didn't recognize that. "
                      "Hit Ctrl-D to quit.")
                ans = None

    def __str__(self):
        return "FileNodeAPI"

    def __iter__(self):
        return self.graph.nodes_iter()


class FileEdgeAPI(api.EdgeAPISpec):

    def __init__(self, G, logger):
        self.G = G
        self.logger = logger

    def get(self, src, dest, **kwargs):
        """Retrieve an edge by id or source & destination."""
        if kwargs is None:  # Single item retrieval
            return self.G.edge[src][dest]

    def add(self, src, dest, type_, **kwargs):
        """Add an edge to the Graph."""
        self.G.add_edge(src, dest, type=type_, **kwargs)

    def update(self, src, dest, **kwargs):
        """Update an edge's attributes."""
        self.G.edge[src][dest] = {**self.G.edge[src][dest], **kwargs}

    def delete(self, src, dest, **kwargs):
        """Delete an edge from the graph."""
        self.G.remove_edge(src, dest)
