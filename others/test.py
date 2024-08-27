import json
from transitions import Machine

class Matter:
    pass

# Definindo a máquina de estados
states = ['solid', 'liquid', 'gas', 'plasma']
transitions = [
    { 'trigger': 'melt', 'source': 'solid', 'dest': 'liquid' },
    { 'trigger': 'evaporate', 'source': 'liquid', 'dest': 'gas' },
    { 'trigger': 'sublimate', 'source': 'solid', 'dest': 'gas' },
    { 'trigger': 'ionize', 'source': 'gas', 'dest': 'plasma' }
]

# Criando a máquina de estados
matter = Matter()
machine = Machine(model=matter, states=states, transitions=transitions, initial='solid')
print(matter.state) # solid