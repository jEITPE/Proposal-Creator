// Arquivo JavaScript para página de gerenciamento de usuários

// Mudar entre as abas
document.addEventListener('DOMContentLoaded', function() {
    // Mudar entre as abas
    document.querySelectorAll('.tab-link').forEach(tab => {
        tab.addEventListener('click', function() {
            // Remover classe active de todas as tabs
            document.querySelectorAll('.tab-link').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Adicionar classe active na tab clicada
            this.classList.add('active');
            document.getElementById(this.getAttribute('data-tab') + '-tab').classList.add('active');
        });
    });
    
    // Pesquisar usuários
    const searchInput = document.getElementById('pesquisar-usuario');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const termo = this.value.toLowerCase();
            const cards = document.querySelectorAll('.user-card');
            
            cards.forEach(card => {
                const nome = card.querySelector('.user-title').textContent.toLowerCase();
                const login = card.querySelector('.user-info-item:first-child span').textContent.toLowerCase();
                
                if (nome.includes(termo) || login.includes(termo)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // Verificar se há algum perfil selecionado
    const perfilSelect = document.getElementById('tipo');
    if (perfilSelect) {
        verificarPerfilSelecionado();
        perfilSelect.addEventListener('change', verificarPerfilSelecionado);
    }
    
    // Inicializar a visualização de blocos
    mostrarCategoria('todos');
});

// Confirmação de remoção
function confirmarRemocao(usuario) {
    document.getElementById('removerUsuario').value = usuario;
    $('#confirmacaoModal').modal('show');
}

// Verificar perfil selecionado para mostrar opções adicionais
function verificarPerfilSelecionado() {
    const perfilSelect = document.getElementById('tipo');
    const opcoesTempo = document.getElementById('opcoes-acesso-temporario');
    const blocoSelecao = document.getElementById('blocos-selecao');
    
    const valorSelecionado = perfilSelect.options[perfilSelect.selectedIndex].value;
    const textoPerfil = perfilSelect.options[perfilSelect.selectedIndex].text;
    
    // Verificar se é um perfil temporário
    if (textoPerfil.includes('Temporário')) {
        opcoesTempo.style.display = 'flex';
    } else {
        opcoesTempo.style.display = 'none';
    }
    
    // Verificar se deve mostrar seleção de blocos
    if (valorSelecionado !== 'admin') {
        blocoSelecao.style.display = 'block';
    } else {
        blocoSelecao.style.display = 'none';
    }
}

// Mostrar categoria específica de blocos
function mostrarCategoria(categoria) {
    // Atualizar abas
    document.querySelectorAll('.blocos-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.blocos-tab[data-categoria="${categoria}"]`).classList.add('active');
    
    // Esconder todas as categorias
    document.querySelectorAll('.categoria-selecao').forEach(cat => {
        cat.style.display = 'none';
    });
    
    // Mostrar a categoria selecionada
    document.querySelector(`.categoria-selecao[data-categoria="${categoria}"]`).style.display = 'block';
}

// Sincronizar checkboxes com mesmo valor
function sincronizarCheckboxes(nomeBloco, checked) {
    document.querySelectorAll(`input[name="blocos_permitidos"][value="${nomeBloco}"]`).forEach(checkbox => {
        checkbox.checked = checked;
    });
}

// Função para selecionar todos os blocos
function selecionarTodosBlocos(selecionar) {
    document.querySelectorAll('input[name="blocos_permitidos"]').forEach(checkbox => {
        checkbox.checked = selecionar;
    });
}

// Substituímos a função que mostrava o popup por console.log
function verificarBlocos() {
    const checkboxes = document.querySelectorAll('input[name="blocos_permitidos"]');
    console.log(`Total de blocos: ${checkboxes.length}\nSelecionados: ${Array.from(checkboxes).filter(c => c.checked).length}`);
}

// Substituímos a função que mostrava o popup por console.log
function criarBlocosManualmente() {
    console.log('Esta função é apenas para depuração e deve ser implementada no servidor.');
} 