#!/bin/bash

echo "Bot Test Suite"
echo "==============="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

run_tests() {
    echo -e "${YELLOW}$1${NC}"
    eval "$2"
    echo ""
}

run_tests "Excutando TODOS os testes:" \
    "pytest bot/tests/ -v"

run_tests "Executando apenas testes UNITÁRIOS:" \
    "pytest bot/tests/ -v -m unit"

run_tests "Executando testes de INTEGRAÇÃO:" \
    "pytest bot/tests/ -v -m integration"

run_tests "Executando com COBERTURA:" \
    "pytest bot/tests/ --cov=bot --cov-report=html --cov-report=term"

run_tests "Executando teste específico (text_utils):" \
    "pytest bot/tests/test_text_utils.py -v"

run_tests "Modo VERBOSO MÁXIMO:" \
    "pytest bot/tests/ -vv -s"

run_tests "Parar no PRIMEIRO ERRO:" \
    "pytest bot/tests/ -x"

run_tests "Re-executar testes que FALHARAM:" \
    "pytest bot/tests/ --lf"

echo -e "${GREEN}Testes concluídos!${NC}"
echo ""
echo "Ver relatórios de cobertura: open htmlcov/index.html"