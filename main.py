import time
import math
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
# Coordenador
class Agente_Coordenador(Agent):
    class SolveExpression(OneShotBehaviour):
        async def on_start(self):
            self.expression = None
            print("Ativando Agente Coordenador")
        async def run(self):
            self.expression = input("Digite a equação: ").replace(" ", "") # Expressão sem espaços
            print(self.expression) # Mostrando a Equação Captada
            
            
            ################################################
            # Codigo pra separar a equação em sub-equações #
            ################################################
            
            ########################################################
            # Codigo para enviar a equação pra cada um dos agentes #
            # if (operador x) -> envie para agente x               # 
            ########################################################
            
            # Removendo os operadores para enviar apenas os numeros
            self.expression = self.expression.replace("+", " ")
            self.expression = self.expression.replace("-", " ")
            
            msg = Message(to="somador@127.0.0.1") # teste mandando pro somador
            msg.body = self.expression
            await self.send(msg)
            msg.to = "subtrator@127.0.0.1" # teste mandando pro subtrator
            await self.send(msg)
        
    async def setup(self):
        self.add_behaviour(self.SolveExpression())

# Somador
class Agente_Somador(Agent):
    class ReceiveMsg(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Somador")
        
        async def run(self):
            msg = await self.receive()
            if msg:
                operando = msg.body.split(" ") # transformando a string num array
                print(f"Agente Somador: Mensagem Recebida, realizando operação {operando[0]} + {operando[1]}")
                resultado = float(operando[0]) + float(operando[1])
                print(f"Agente Somador: Calculo realizado, o resultado é {resultado}")
                
                # Codigo para enviar o resultado do calculo de volta
                # sender = msg.sender
                # msg = Message(to=str(sender))
                # msg.body = str(resultado)
                # await self.send(msg)
                # print(f'Agente Somador: Resposta enviada')
                # time.sleep(5)

    async def setup(self):
        self.add_behaviour(self.ReceiveMsg())

# Subtrator
class Agente_Subtrator(Agent):
    class ReceiveMsg(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Subtrator")
        async def run(self):
            msg = await self.receive()
            if msg:
                operando = msg.body.split(" ") # transformando a string num array
                print(f"Agente Subtrator: Mensagem Recebida, realizando operação {operando[0]} - {operando[1]}")
                resultado = float(operando[0]) - float(operando[1])
                print(f"Agente Subtrator: Calculo realizado, o resultado é {resultado}")
                
                # Codigo para enviar o resultado do calculo de volta
                # sender = msg.sender
                # msg = Message(to=str(sender))
                # msg.body = str(resultado)
                # await self.send(msg)
                # print(f'Agente Somador: Resposta enviada')
                # time.sleep(5)

    async def setup(self):
        self.add_behaviour(self.ReceiveMsg())

# Main
if __name__ == "__main__":
    
    somador = Agente_Somador("somador@127.0.0.1", "spade2000")
    future = somador.start()
    future.result()
    
    subtrator = Agente_Subtrator("subtrator@127.0.0.1", "spade2000")
    future = subtrator.start()
    future.result()
    
    coordenador = Agente_Coordenador("admin@127.0.0.1", "spade2000")
    future = coordenador.start()
    future.result()

    while coordenador.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            somador.stop()
            subtrator.stop()
            coordenador.stop()
            break
    print("Os Agentes Foram Desativados")