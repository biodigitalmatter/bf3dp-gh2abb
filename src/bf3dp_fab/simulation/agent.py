from uuid import uuid4

from compas.geometry import Point

class Agent(object):
    def __init__(self, name_prefix="agent_", initial_position=[0,0,0], initial_attributes=None):
        self.name = name_prefix + uuid4()
        self.position = Point(*initial_position)
        self.attributes = initial_attributes or {}
        
    
