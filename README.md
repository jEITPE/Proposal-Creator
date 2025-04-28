# Sistema de Geração de Propostas Service IT

Um sistema web desenvolvido em Python/Flask para automatizar a criação de propostas comerciais para a Service IT.

## Funcionalidades

- Criação de propostas personalizadas
- Edição de blocos de conteúdo
- Visualização em tempo real
- Gerenciamento de usuários
- Diferentes tipos de ofertas (Workplace, Infraestrutura, Cloud, Segurança, Governança)
- Auto-save de rascunhos
- Exportação para DOCX

## Tecnologias Utilizadas

- Python 3.x
- Flask
- HTML/CSS/JavaScript
- Quill.js (editor de texto rico)
- python-docx (geração de documentos)

## Instalação

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/gerador-propostas-service-it.git
cd gerador-propostas-service-it
```

2. Instale as dependências:
```
pip install -r requirements.txt
```

3. Execute a aplicação:
```
python app.py
```

4. Acesse a aplicação em seu navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

- `app.py`: Arquivo principal da aplicação
- `templates/`: Arquivos HTML
- `static/`: Arquivos estáticos (CSS, JS, imagens)
- `data/`: Arquivos JSON para armazenamento de dados
- `uploads/`: Pasta para upload de logos de clientes
- `propostas_geradas/`: Pasta para armazenar as propostas geradas

## Usuários Padrão

- Administrador: `admin` / `admin123`
- AM: `serviceit` / `serviceit123`

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um novo Pull Request

## Licença

Este projeto é licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

# Sistema de Permissionamento

## Novos recursos

Foram adicionados novos recursos ao sistema de permissionamento:

1. **Novos grupos de usuários**:
   - Marketing
   - RH
   - Temporário (com acesso por 24 horas)

2. **Permissionamento por blocos**:
   - Administradores podem definir quais blocos cada usuário pode editar
   - Interface para gerenciar blocos e suas permissões
   - Superusuários têm acesso a todos os blocos

3. **Acesso temporário**:
   - O sistema verifica automaticamente se o acesso temporário expirou
   - Após 24 horas, o acesso é revogado automaticamente

## Como utilizar

### Gerenciamento de Usuários

Agora é possível definir se um usuário é superusuário e quais blocos ele pode editar. O sistema de gerenciamento de usuários permite:

- Criar usuários com diferentes perfis (Marketing, RH, Temporário, etc.)
- Definir usuários como superusuários (acesso a todos os blocos)
- Atribuir permissões específicas para blocos

### Gerenciamento de Blocos

A nova interface de gerenciamento de blocos permite:

- Criar novos blocos com título e conteúdo
- Definir quais usuários podem editar cada bloco
- Marcar blocos como obrigatórios
- Remover blocos não utilizados

Acesse estas funcionalidades através do menu de Administração no painel lateral. 