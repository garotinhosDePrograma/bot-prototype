"""
Script de teste para o Bot Worker refatorado (versão modular).
Execute: python teste_bot.py
"""

from bot.bot_worker import BotWorker
import time
import json
from datetime import datetime
import os

# Diretório de logs
LOGS_DIR = "bot/logs"

def criar_diretorio_logs():
    """Cria diretório de logs se não existir."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        print(f"📁 Diretório '{LOGS_DIR}/' criado.\n")

def gerar_nome_arquivo_log(prefixo: str) -> str:
    """Gera nome de arquivo de log com timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(LOGS_DIR, f"{prefixo}_{timestamp}.json")

def linha():
    print("=" * 70)

def salvar_log(arquivo_log: str, pergunta: str, resultado: dict, tempo_total: float = None, logs_processo: list = None):
    """
    Salva pergunta, resposta e metadados em arquivo JSON específico.

    Args:
        arquivo_log: Caminho do arquivo de log
        pergunta: Pergunta do usuário
        resultado: Resultado do process_query
        tempo_total: Tempo total (opcional)
        logs_processo: Lista de logs detalhados do processo (opcional)
    """
    try:
        criar_diretorio_logs()

        # Carrega logs existentes do arquivo
        logs = []
        if os.path.exists(arquivo_log):
            try:
                with open(arquivo_log, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception as e:
                print(f"⚠️  Aviso: Erro ao carregar logs de {arquivo_log}: {e}")
                logs = []

        # Cria entrada de log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "pergunta": pergunta,
            "resposta": resultado.get('response', ''),
            "fonte": resultado.get('source', ''),
            "status": resultado.get('status', 'unknown'),
            "tempo_processamento": resultado.get('processing_time', tempo_total),
            "erro": resultado.get('message', '') if resultado.get('status') == 'error' else None,
            "processo": logs_processo if logs_processo else []
        }

        # Adiciona ao histórico
        logs.append(log_entry)

        # Salva de volta no arquivo
        try:
            with open(arquivo_log, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ ERRO ao salvar logs em {arquivo_log}: {e}")
            # Tenta salvar em arquivo de backup
            backup_file = f"{arquivo_log}.backup_{int(time.time())}"
            try:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
                print(f"✅ Logs salvos em arquivo de backup: {backup_file}")
            except:
                print(f"❌ Não foi possível salvar nem no backup")

    except Exception as e:
        print(f"❌ ERRO ao processar log: {e}")
        print(f"DEBUG - Log que falhou: {pergunta} -> {resultado}")

def limpar_logs():
    """Remove todos os arquivos de log do diretório."""
    if os.path.exists(LOGS_DIR):
        arquivos = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]
        if arquivos:
            for arquivo in arquivos:
                os.remove(os.path.join(LOGS_DIR, arquivo))
            print(f"✅ {len(arquivos)} arquivo(s) de log removido(s).\n")
        else:
            print(f"ℹ️  Nenhum arquivo de log para remover.\n")
    else:
        print(f"ℹ️  Diretório de logs não existe.\n")

def teste_basico():
    """Teste básico com várias perguntas."""
    print("\n🤖 TESTE BÁSICO DO BOT\n")
    linha()

    # Cria arquivo de log para este teste
    arquivo_log = gerar_nome_arquivo_log("bot_logs_basico")
    print(f"📝 Logs serão salvos em: {arquivo_log}\n")

    bot = BotWorker()
    print("✅ Bot inicializado!\n")

    perguntas = [
        "Oi, tudo bem?",
        "Qual a capital da França?",
        "Como funciona a fotossíntese?",
        "Por que o céu é azul?",
        "Quem foi Albert Einstein?",
        "Quando foi descoberto o Brasil?",
    ]

    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n[{i}/{len(perguntas)}] {pergunta}")
        print("-" * 70)

        resultado = bot.process_query(pergunta)

        # Salva no log específico deste teste
        salvar_log(arquivo_log, pergunta, resultado, logs_processo=resultado.get('logs_processo', []))

        if resultado['status'] == 'success':
            print(f"Resposta: {resultado['response']}")
            print(f"Fonte(s): {resultado['source']}")
            print(f"Tempo: {resultado['processing_time']}s")
        else:
            print(f"❌ Erro: {resultado['message']}")

    linha()
    print(f"\n✨ Teste concluído! Logs salvos em '{arquivo_log}'\n")

def teste_cache():
    """Testa o sistema de cache."""
    print("\n⚡ TESTE DE CACHE\n")
    linha()

    # Cria arquivo de log para este teste
    arquivo_log = gerar_nome_arquivo_log("bot_logs_cache")
    print(f"📝 Logs serão salvos em: {arquivo_log}\n")

    bot = BotWorker()
    pergunta = "Qual a capital do Brasil?"

    print(f"Pergunta: {pergunta}\n")

    # Primeira vez (busca nas APIs)
    print("[1ª tentativa - busca nas APIs]")
    resultado1 = bot.process_query(pergunta)
    salvar_log(arquivo_log, f"{pergunta} [1ª tentativa]", resultado1, logs_processo=resultado1.get('logs_processo', []))
    print(f"Tempo: {resultado1['processing_time']}s")
    print(f"Fonte: {resultado1['source']}\n")

    # Segunda vez (deve vir do cache)
    print("[2ª tentativa - deve vir do cache]")
    resultado2 = bot.process_query(pergunta)
    salvar_log(arquivo_log, f"{pergunta} [2ª tentativa - cache]", resultado2, logs_processo=resultado2.get('logs_processo', []))
    print(f"Tempo: {resultado2['processing_time']}s")
    print(f"Fonte: {resultado2['source']}\n")

    melhoria = (1 - resultado2['processing_time'] / resultado1['processing_time']) * 100
    print(f"Melhoria: {melhoria:.1f}% mais rápido")

    linha()
    print(f"\n✨ Logs salvos em '{arquivo_log}'\n")

def teste_combinacao():
    """Testa a combinação de múltiplas fontes."""
    print("\n🔗 TESTE DE COMBINAÇÃO DE FONTES\n")
    linha()

    # Cria arquivo de log para este teste
    arquivo_log = gerar_nome_arquivo_log("bot_logs_combinacao")
    print(f"📝 Logs serão salvos em: {arquivo_log}\n")

    bot = BotWorker()

    # Perguntas explicativas (devem usar múltiplas fontes)
    perguntas = [
        "Como funciona um motor a combustão?",
        "Por que o mar é salgado?",
        "Como surgiu o universo?"
    ]

    for pergunta in perguntas:
        print(f"\nPergunta: {pergunta}")
        print("-" * 70)

        resultado = bot.process_query(pergunta)

        # Salva no log específico deste teste
        salvar_log(arquivo_log, pergunta, resultado, logs_processo=resultado.get('logs_processo', []))

        if resultado['status'] == 'success':
            print(f"Resposta: {resultado['response']}")
            print(f"Fonte(s): {resultado['source']}")

            # Verifica se usou múltiplas fontes
            if '+' in resultado['source']:
                print("✅ Múltiplas fontes combinadas!")
            else:
                print("ℹ️  Uma fonte principal")
        else:
            print(f"❌ Erro: {resultado['message']}")

    linha()
    print(f"\n✨ Logs salvos em '{arquivo_log}'\n")

def modo_interativo():
    """Modo interativo para conversar com o bot."""
    print("\n💬 MODO INTERATIVO\n")
    linha()

    # Cria arquivo de log para este teste
    arquivo_log = gerar_nome_arquivo_log("bot_logs_interativo")
    print(f"📝 Logs serão salvos em: {arquivo_log}")
    print("Digite suas perguntas ou 'sair' para voltar\n")

    bot = BotWorker()

    while True:
        try:
            pergunta = input("Você: ").strip()

            if not pergunta:
                continue

            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\nVoltando...\n")
                break

            resultado = bot.process_query(pergunta)

            # Salva no log específico deste teste
            salvar_log(arquivo_log, pergunta, resultado, logs_processo=resultado.get('logs_processo', []))

            if resultado['status'] == 'success':
                print(f"Bot: {resultado['response']}")
                print(f"     (fonte: {resultado['source']}, {resultado['processing_time']}s)\n")
            else:
                print(f"Bot: ❌ {resultado['message']}\n")

        except KeyboardInterrupt:
            print("\n\nVoltando...\n")
            break
        except Exception as e:
            print(f"❌ Erro: {e}\n")

def visualizar_logs():
    """Mostra os logs salvos."""
    print("\n📋 LOGS SALVOS\n")
    linha()

    if not os.path.exists(LOGS_DIR):
        print("Nenhum log encontrado. Execute um teste primeiro.\n")
        return

    # Lista todos os arquivos de log
    arquivos_log = [f for f in os.listdir(LOGS_DIR) if f.endswith('.json')]

    if not arquivos_log:
        print("Nenhum arquivo de log encontrado.\n")
        return

    print(f"Arquivos de log disponíveis ({len(arquivos_log)}):")
    for i, arquivo in enumerate(sorted(arquivos_log), 1):
        print(f"  {i}. {arquivo}")

    print()
    escolha = input("Digite o número do arquivo para visualizar (ou Enter para ver todos): ").strip()

    if escolha:
        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(arquivos_log):
                arquivos_selecionados = [sorted(arquivos_log)[idx]]
            else:
                print("❌ Número inválido!\n")
                return
        except ValueError:
            print("❌ Entrada inválida!\n")
            return
    else:
        arquivos_selecionados = sorted(arquivos_log)

    # Mostra logs dos arquivos selecionados
    for arquivo in arquivos_selecionados:
        print(f"\n{'='*70}")
        print(f"📄 {arquivo}")
        print('='*70)

        try:
            caminho = os.path.join(LOGS_DIR, arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            if not logs:
                print("Arquivo vazio.\n")
                continue

            print(f"Total de registros: {len(logs)}\n")

            for i, log in enumerate(logs, 1):
                print(f"[{i}] {log['timestamp']}")
                print(f"    Pergunta: {log['pergunta']}")
                print(f"    Resposta: {log['resposta'][:100]}{'...' if len(log['resposta']) > 100 else ''}")
                print(f"    Fonte: {log['fonte']}")
                print(f"    Status: {log['status']}")
                print(f"    Tempo: {log['tempo_processamento']}s")
                if log.get('erro'):
                    print(f"    Erro: {log['erro']}")
                if log.get('processo'):
                    print(f"    Etapas do processo: {len(log['processo'])} registradas")
                print()

        except Exception as e:
            print(f"❌ Erro ao ler {arquivo}: {e}\n")

    linha()
    print(f"\nLogs completos em: {LOGS_DIR}/\n")

def menu():
    """Menu principal."""
    while True:
        print("\n" + "="*70)
        print("🤖 BOT WORKER - MENU DE TESTES")
        print("="*70)
        print("\n1. Teste básico")
        print("2. Teste de cache")
        print("3. Teste de combinação de fontes")
        print("4. Modo interativo")
        print("5. Visualizar logs")
        print("6. Limpar logs")
        print("7. Sair")
        print()

        escolha = input("Escolha: ").strip()

        if escolha == "1":
            teste_basico()
        elif escolha == "2":
            teste_cache()
        elif escolha == "3":
            teste_combinacao()
        elif escolha == "4":
            modo_interativo()
        elif escolha == "5":
            visualizar_logs()
        elif escolha == "6":
            limpar_logs()
        elif escolha == "7":
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida!")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\n👋 Programa encerrado.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")