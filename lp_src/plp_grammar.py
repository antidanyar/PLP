import warnings
warnings.filterwarnings("ignore")
import networkx as nx

class PLPgrammar:
    def __init__(self):
        self.rules = list()

    def rules(self):
        return self.rules

    def set_rules(self, rules):
        self.rules = rules

    def add(self, rule):
        self.rules.append(rule)

    def remove(self, rule):
        self.rules.remove(rule)

    def apply(self, uf):
        sf = uf
        for rule in self.rules:
            sf = rule.apply(sf)
        return sf

    def order_rules(self, vocab):
        if len(self) <= 1: # can't order one rule
            return
        nodes = list(self.rules)
        edges = list()
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                ri, rj = nodes[i], nodes[j]
                if ri.more_specific(rj, vocab):
                    edges.append((ri, rj))
                elif rj.more_specific(ri, vocab):
                    edges.append((rj, ri))
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        ordered_rules = list(nx.topological_sort(G))

        self.rules = ordered_rules

    def order_rules_by_scope(self, vocab):
        if len(self) <= 1: # can't order one rule
            return
        rule_scopes = list((r, r.get_n_c(vocab)[0]) for r in self.rules)
        self.rules = list(r for r, _ in sorted(rule_scopes, key=lambda it: it[-1]))

    def __iter__(self):
        return self.rules.__iter__()

    def __contains__(self, rule):
        '''
        :rule: a rule

        :return: True if the :rule: is in the grammar, False if not
        '''
        return rule in self.rules

    def __getitem__(self, idx):
        return self.rules[idx]
    
    def __setitem__(self, idx, rule):
        self.rules[idx] = rule

    def __len__(self):
        return len(self.rules)

    def __str__(self):
        s = ''
        for i, r in enumerate(self.rules):
            s += f'{i + 1}: {r}\n'
        return s[:-1] # trim final word end

    def __repr__(self):
        return self.__str__()