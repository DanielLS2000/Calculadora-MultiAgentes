import time
import math
import sys
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message

# Coordenador
class AgenteCoordenador(Agent):
    class ResolucaoDeExpressao(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Coordenador")
            self.expressao = None
            
        async def run(self):
            self.expressao = ""

            while self.expressao == "":
                self.expressao = input("Digite uma expressão: ").replace(" ", "")

            print(self.expressao) # Mostrando a Equação Captada
            valores = []
            operacoes = []
            i = 0

            while i < len(self.expressao):
                caracter = self.expressao[i]

                # Marca o início de uma expressão entre parênteses.
                if caracter == "(":
                    operacoes.append(caracter)

                # Se o caracter for numérico, descobre e extrai o número completo(operando).
                elif caracter.isdigit():
                    valores, i = self.retornar_operando(valores, self.expressao, i)
                # Se encontrar um ")", resolver subexpressão até encontrar "("
                elif caracter == ")":
                    while len(operacoes) != 0 and operacoes[-1] != "(":
                        valores, operacoes = await self.resolver_subexpressao(valores, operacoes)

                    operacoes.pop() # Remove o "(" correspondente ao ")" acima. 

                # O caracter atual é uma operaçao. É necessário comparar a operação atual com a última salva.
                else:
                    # Se o menos for sinal, em vez de operação
                    if caracter == "-" and self.eh_sinal_negativo(self.expressao, i):
                        caracter = "!"

                    # Se a operação do topo, tiver prioriadade superior, resolvê-la.
                    while len(operacoes) != 0 and self.retornar_precedencia(operacoes[-1]) >= self.retornar_precedencia(caracter):
                        valores, operacoes = await self.resolver_subexpressao(valores, operacoes)

                    # adiciona operação atual a pilha
                    operacoes.append(caracter)

                i += 1

            while len(operacoes) != 0:
                valores, operacoes = await self.resolver_subexpressao(valores, operacoes)

            print(f"Resultado final: {valores.pop()}") # O que estiver no topo é o resultado da subexpressao

        # Retorna o nível de prioridade da operação.
        def retornar_precedencia(self, operacao):
            if operacao == '+' or operacao == '-':
                return 1

            if operacao == 'x' or operacao == '/':
                return 2

            if operacao == "^" or operacao == "#":
                return 3

            if operacao == "!":
                return 4

            return 0

        def retornar_operando(self, valores, expressao, i):
            j = i
            valor = ""
            # Enquanto o próximo caracter for numérico
            while (j < len(expressao) and (expressao[j].isdigit() or expressao[j] == ".")):
                valor += expressao[j]
                j += 1

            valor = float(valor)
            valores.append(valor)

            j -= 1 # Volta para o indíce anterior, porque o loop para em um caracter não numérico, que ainda deve ser analisado.
            return valores, j

        # Determina se um "-" é sinal ou operação.
        def eh_sinal_negativo(self, expressao, i):
            j = i - 1
            eh_sinal = True

            if j >= 0 and (expressao[j].isdigit() or expressao[j] == ")"):
                    eh_sinal = False

            return eh_sinal

        # Resolve a subexpressao de maior prioridade, retornando as pilhas de valores e operacoes atualizadas
        async def resolver_subexpressao(self, valores, operacoes):
            operacao = operacoes.pop()

            # raiz quadrada é uma operação unária
            if operacao == "#" or operacao == "!":
                valor = valores.pop()
                resultado = await self.enviar_para_agente_responsavel(operacao, valor)

            else:
                valor2 = valores.pop()
                valor1 = valores.pop()
                resultado = await self.enviar_para_agente_responsavel(operacao, valor1, valor2)

            valores.append(resultado)
            
            return valores, operacoes
                
        async def enviar_para_agente_responsavel(self, operacao, valor1, valor2 = None):
            msg = Message()

            if operacao == "#" or operacao == "!":
                msg.body = f"{valor1}"

                if operacao == "#":
                    if valor1 < 0:
                        print("Não existem raizes quadradas reais negativas!")
                        sys.exit()

                    msg.to = "agente_raiz@127.0.0.1" 
                    msg.metadata = {"operator" : "#", "value1" : valor1, "value2" : None}

                else:
                    msg.to = "agente_sinal@127.0.0.1" 
                    msg.metadata = {"operator" : "!", "value1" : valor1, "value2" : None}
                
            else:
                msg.body = f"{valor1} {valor2}"

                if operacao == "+":
                    msg.to = "agente_soma@127.0.0.1"
                    msg.metadata = {"operator" : "+", "value1" : valor1, "value2" : valor2}

                elif operacao == "-":
                    msg.to = "agente_subtracao@127.0.0.1"
                    msg.metadata = {"operator" : "-", "value1" : valor1, "value2" : valor2}

                elif operacao == "x":
                    msg.to = "agente_multiplicacao@127.0.0.1" 
                    msg.metadata = {"operator" : "x", "value1" : valor1, "value2" : valor2}

                elif operacao == "/":
                    if valor2 == 0:
                        print("Não é permitido dividir por zero!")
                        sys.exit()

                    msg.to = "agente_divisao@127.0.0.1"
                    msg.metadata = {"operator" : "/", "value1" : valor1, "value2" : valor2}

                elif operacao == "^":
                    msg.to = "agente_potencia@127.0.0.1"
                    msg.metadata = {"operator" : "^", "value1" : valor1, "value2" : valor2}

            await self.send(msg)
            resultado = await self.receive(timeout = 60)
            resultado = float(resultado.body)
            return resultado

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeExpressao())

# Somador
class AgenteSoma(Agent):
    class ResolucaoDeSoma(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Somador")
        
        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1, valor2 = msg.body.split()
                resultado = float(valor1) + float(valor2)
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata = metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeSoma())

# Subtrator
class AgenteSubtracao(Agent):
    class ResolucaoDeSubtracao(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Subtrator")

        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1, valor2 = msg.body.split()
                resultado = float(valor1) - float(valor2)              
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata = metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeSubtracao())

class AgenteMultiplicacao(Agent):
    class ResolucaoDeMultiplicacao(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Multiplicador")

        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1, valor2 = msg.body.split()
                resultado = float(valor1) * float(valor2)
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata = metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeMultiplicacao())

class AgenteDivisao(Agent):
    class ResolucaoDeDivisao(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente da divisao")

        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1, valor2 = msg.body.split()
                resultado = float(valor1) / float(valor2)
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata = metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeDivisao())

class AgentePotencia(Agent):
    class ResolucaoDePotencia(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente da potencia")

        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1, valor2 = msg.body.split()
                resultado = float(valor1) ** float(valor2)
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDePotencia())

# Raiz quadrada
class AgenteRaizQuadrada(Agent):
    class ResolucaoDeRaizQuadrada(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente Raiz Quadrada")
            
        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor = msg.body
                resultado = float(valor) ** (1/2) 
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeRaizQuadrada())

class AgenteSinal(Agent):
    class ResolucaoDeSinal(CyclicBehaviour):
        async def on_start(self):
            print("Ativando Agente do sinal")
        
        async def run(self):
            msg = await self.receive()
            
            if msg:
                valor1 = msg.body
                resultado = -float(valor1)
                
                # Codigo para enviar o resultado do calculo de volta
                sender = msg.sender
                metadata = msg.metadata
                msg = Message(to=str(sender))
                msg.body = str(resultado)
                msg.metadata = metadata
                await self.send(msg)

    async def setup(self):
        self.add_behaviour(self.ResolucaoDeSinal())

# Main
if __name__ == "__main__":
    agente_soma = AgenteSoma("agente_soma@127.0.0.1", "12345678")
    future = agente_soma.start()
    future.result()

    agente_subtracao = AgenteSubtracao("agente_subtracao@127.0.0.1", "12345678")
    future = agente_subtracao.start()
    future.result()

    agente_multiplicacao = AgenteMultiplicacao("agente_multiplicacao@127.0.0.1", "12345678")
    future = agente_multiplicacao.start()
    future.result()

    agente_divisao = AgenteDivisao("agente_divisao@127.0.0.1", "12345678")
    future = agente_divisao.start()
    future.result()

    agente_potencia = AgentePotencia("agente_potencia@127.0.0.1", "12345678")
    future = agente_potencia.start()
    future.result()

    agente_raiz_quadrada = AgenteRaizQuadrada("agente_raiz@127.0.0.1", "12345678")
    future = agente_raiz_quadrada.start()
    future.result()

    agente_sinal = AgenteSinal("agente_sinal@127.0.0.1", "12345678")
    future = agente_sinal.start()
    future.result()

    agente_coordenador = AgenteCoordenador("agente_coordenador@127.0.0.1", "12345678")
    future = agente_coordenador.start()
    future.result()

    while agente_coordenador.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            agente_soma.stop()
            agente_subtracao.stop()
            agente_multiplicacao.stop()
            agente_divisao.stop()
            agente_potencia.stop()
            agente_raiz_quadrada.stop()
            agente_sinal.stop()
            agente_coordenador.stop()
            break

    print("Os Agentes Foram Desativados")