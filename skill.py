import math
import copy

class Skill:

    @classmethod
    def from_dict(cls, data):
        local_data = {}
        for field in ["name", "skill_list", "cost", "build"]:
            if field in data:
                field_data = copy.deepcopy(data[field])
                local_data[field] = field_data
        return cls(**local_data)


    def __init__(self, name, skill_list, cost, build):
        self.name = name
        self.skill_list = skill_list
        self.cost = cost
        self.build = build

    def get_name(self, class_number):
        multiplier = 1 + math.floor(class_number / 2) 
        build_cost = int(self.build) * multiplier
        name_cost = " " + self.cost if self.cost else ""
        return self.name + " (" + str(build_cost) + ")" + name_cost

    def as_dict(self):
        data = {}
        for field in self._fields:
            value = getattr(self, field)
            data[field] = value
        return data

    def __str__(self):
        return self.get_name(1)
