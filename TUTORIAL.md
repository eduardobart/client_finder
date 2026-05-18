# Tutorial de Instalação — Client Finder

> Guia passo a passo para instalar e usar o Client Finder mesmo sem experiência com programação.

---

## O que você vai precisar

- Computador com Windows 10 ou 11
- Conexão com a internet
- Cerca de 15 minutos para a instalação inicial

---

## Passo 1 — Instalar o Python

O Python é o programa que faz o Client Finder funcionar.

1. Acesse **https://www.python.org/downloads/**
2. Clique no botão amarelo grande **"Download Python 3.x.x"**
3. Abra o arquivo baixado (ex: `python-3.12.x-amd64.exe`)
4. **IMPORTANTE:** Marque a opção **"Add Python to PATH"** antes de instalar

   ![Marque Add Python to PATH](https://docs.python.org/3/_images/win_installer.png)

5. Clique em **"Install Now"**
6. Aguarde a instalação terminar e clique em **"Close"**

**Verificar se funcionou:**
- Abra o menu Iniciar, digite `cmd` e pressione Enter
- Digite o comando abaixo e pressione Enter:
  ```
  python --version
  ```
- Deve aparecer algo como `Python 3.12.x`

---

## Passo 2 — Baixar o Client Finder

1. Acesse **https://github.com/eduardobart/client_finder**
2. Clique no botão verde **"Code"**
3. Clique em **"Download ZIP"**
4. Salve o arquivo em um lugar fácil de encontrar (ex: sua **Área de Trabalho**)
5. Clique com o botão direito no arquivo ZIP e escolha **"Extrair Tudo..."**
6. Escolha onde extrair (ex: `C:\client_finder`) e clique em **Extrair**

---

## Passo 3 — Abrir o Terminal na pasta do projeto

1. Abra o **Explorador de Arquivos** e navegue até a pasta extraída (`client_finder`)
2. Clique na barra de endereço no topo da janela (onde aparece o caminho da pasta)
3. Digite `cmd` e pressione **Enter**
4. Uma janela preta (terminal) vai abrir já dentro da pasta correta

---

## Passo 4 — Instalar as dependências

No terminal que abriu, copie e cole o comando abaixo e pressione **Enter**:

```
python -m pip install -r requirements.txt
```

Vai aparecer uma série de textos sendo baixados e instalados. Aguarde terminar (pode levar 2-5 minutos).

Quando terminar, vai aparecer algo como `Successfully installed ...`

---

## Passo 5 — Abrir a interface web

No mesmo terminal, cole o comando abaixo e pressione **Enter**:

```
streamlit run app.py
```

Após alguns segundos, o seu **navegador vai abrir automaticamente** com a interface do Client Finder.

Se não abrir, acesse manualmente: **http://localhost:8501**

---

## Como usar

### Busca de demonstração (sem precisar de internet)

1. No campo **"Endereço central"**, digite um endereço (ex: `Av. Paulista, 1000, São Paulo, SP`)
2. Em **"Fonte de dados"**, selecione **"Demo (sem internet)"**
3. Clique em **"Buscar"**
4. Vai aparecer uma tabela com empresas e um mapa interativo

> O modo Demo mostra dados fictícios apenas para você conhecer a interface.

### Busca real (com dados completos da Receita Federal)

Para buscar empresas reais, é necessário baixar os dados oficiais da Receita Federal uma única vez.

> **Atenção:** este download é grande (~5 GB) e pode levar 30 a 60 minutos.

1. Abra um **novo terminal** na pasta do projeto (repita o Passo 3)
2. Digite o comando:
   ```
   python main.py import --yes
   ```
3. Aguarde o download e importação terminar
4. Volte para a interface web, selecione **"Full (Receita Federal)"** e busque normalmente

---

## Fechar e reabrir depois

Para usar o Client Finder em outro momento:

1. Abra o terminal na pasta do projeto (Passo 3)
2. Digite:
   ```
   streamlit run app.py
   ```
3. A interface abre no navegador

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| `python` não é reconhecido | Reinstale o Python marcando "Add Python to PATH" |
| `streamlit` não é reconhecido | Rode novamente o Passo 4 |
| Página não abre no navegador | Acesse manualmente http://localhost:8501 |
| Erro no import da Receita Federal | Verifique sua conexão e tente novamente |

---

## Dúvidas?

Abra uma issue em: **https://github.com/eduardobart/client_finder/issues**
