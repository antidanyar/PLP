from rule import Rule

class Discrepancies(dict):
    def get_rules(self):
        rules = list()
        for rule in self.values():
            if type(rule) is Rule:
                rules.append(rule)
            else: # in case of mutual exclusivity
                rules.extend(rule)
        return rules