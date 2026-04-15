# Security Policy

## Versão suportada

Este projeto é uma aplicação interna de uso operacional. Apenas a versão atual em produção (branch `main`) recebe correções de segurança.

---

## Relatando uma vulnerabilidade

Se você identificar uma vulnerabilidade de segurança neste projeto, **não abra uma issue pública**. Entre em contato diretamente com o responsável pelo projeto:

- **Responsável:** Samuel Freitas
- **E-mail:** samblackbug15@gmail.com

Descreva o problema com o máximo de detalhes possível:
- Componente afetado (ex: `core/database.py`, `pages/importacao.py`)
- Passos para reproduzir
- Impacto potencial estimado

Você receberá uma resposta em até **3 dias úteis**.

---

## Gestão de credenciais

### Ambiente local

- Todas as credenciais (URLs de banco de dados, senha de importação) ficam **exclusivamente** no arquivo `.env`, que está no `.gitignore` e nunca deve ser versionado.
- Use `.env.example` como referência de quais variáveis são necessárias, sem nenhum valor real.

### Produção (Streamlit Cloud)

- As variáveis de ambiente são configuradas em **Settings → Secrets** no painel do Streamlit Community Cloud.
- **Nunca** insira credenciais diretamente no código-fonte ou em arquivos versionados.
- Se suspeitar que uma credencial foi exposta acidentalmente, **regenere imediatamente** as senhas/tokens no Neon.tech e atualize os secrets no Streamlit Cloud.

### Verificação periódica

- Rodar `git log --all -- .env` periodicamente para confirmar que o arquivo nunca foi commitado.
- Em caso de commit acidental de credenciais, siga o procedimento de [remoção do histórico do Git](https://docs.github.com/pt/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) **e** regenere todas as credenciais expostas imediatamente.

---

## Controle de acesso à importação

- A página de Importação é protegida por senha via variável `SENHA_IMPORTACAO`.
- A senha deve ter no mínimo 12 caracteres, com letras maiúsculas, minúsculas, números e símbolos.
- **Não compartilhe** a senha por e-mail, Slack ou qualquer canal não seguro.
- Em caso de comprometimento da senha, atualize `SENHA_IMPORTACAO` no `.env` local e nos Secrets do Streamlit Cloud.

---

## Banco de dados

- Todas as conexões utilizam `sslmode=require` (TLS obrigatório).
- Os bancos estão hospedados no **Neon.tech** com acesso restrito por credenciais únicas por banco.
- Nenhuma query aceita entrada direta do usuário sem parametrização (`%s` via psycopg2).
- Não há execução de SQL dinâmico construído com f-strings ou concatenação de strings de usuário.

---

## Upload de arquivos

- Apenas arquivos `.xlsx` e `.xls` são aceitos na importação.
- O conteúdo dos arquivos é processado em memória (sem gravação em disco no servidor).
- Arquivos malformados geram exceção controlada — o sistema não trava.

---

## Dependências

- As dependências estão fixadas com versões mínimas em `requirements.txt`.
- Recomenda-se auditar periodicamente com `pip audit` ou `safety check`.

---

## O que este projeto NÃO faz

- Não armazena senhas de usuários finais.
- Não expõe endpoints de API públicos.
- Não processa dados de pagamento ou informações pessoais sensíveis (PII) além de dados operacionais internos.
