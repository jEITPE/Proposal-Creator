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