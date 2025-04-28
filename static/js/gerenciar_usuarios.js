// Funções para interface de gerenciamento de usuários
document.addEventListener('DOMContentLoaded', function() {
    console.log("Script de gerenciamento de usuários carregado");
    
    // Gerenciamento de tabs
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function() {
            const tab = this.getAttribute('data-tab');
            
            // Alternar links ativos
            tabLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Alternar conteúdo
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
            
            // Se estiver na aba de adicionar usuário, verificar os blocos
            if (tab === 'adicionar') {
                setTimeout(verificarBlocos, 100);
            }
        });
    });
    
    // Filtro de pesquisa para usuários
    const pesquisarInput = document.getElementById('pesquisar-usuario');
    if (pesquisarInput) {
        const userCards = document.querySelectorAll('.user-card');
        
        pesquisarInput.addEventListener('input', function() {
            const termo = this.value.toLowerCase();
            
            userCards.forEach(card => {
                const nome = card.querySelector('.user-title').textContent.toLowerCase();
                const login = card.querySelector('.user-info-item:first-child span').textContent.toLowerCase();
                
                if (nome.includes(termo) || login.includes(termo)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // Verificação inicial dos blocos
    verificarBlocos();
    
    // Adicionar evento para o botão de mostrar blocos
    const mostrarBlocosBtn = document.querySelector('button[onclick="document.getElementById(\'blocos-selecao\').style.display=\'block\'"]');
    if (mostrarBlocosBtn) {
        mostrarBlocosBtn.addEventListener('click', function() {
            const blocosSelecao = document.getElementById('blocos-selecao');
            blocosSelecao.style.display = 'block';
            
            // Verificar se os blocos estão sendo exibidos
            setTimeout(verificarBlocos, 100);
        });
    }
    
    // Adicionar eventos para os botões de tipo de acesso
    const radioButtons = document.querySelectorAll('input[name="tipo_acesso"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            toggleBlocosAcesso(this.value);
        });
    });
});

// Função para verificar e exibir os blocos disponíveis
function verificarBlocos() {
    const blocosSelecao = document.getElementById('blocos-selecao');
    const blocos = document.querySelectorAll('.user-check-item');
    
    console.log("Verificando blocos...");
    console.log("Total de blocos encontrados:", blocos.length);
    
    // Log detalhado de cada bloco para depuração
    blocos.forEach((bloco, index) => {
        const label = bloco.querySelector('label');
        if (label) {
            console.log(`Bloco ${index + 1}:`, label.textContent);
        } else {
            console.log(`Bloco ${index + 1}: Sem label`);
        }
    });
    
    // Se tivermos poucos blocos, exibir a área automaticamente
    if (blocos.length > 0 && blocos.length < 10) {
        console.log("Exibindo área de seleção de blocos automaticamente");
        
        // Forçar a exibição do container de blocos e todos os blocos
        blocosSelecao.style.display = 'block';
        document.querySelector('.user-check-container').style.display = 'flex';
        
        // Garantir que todos os blocos sejam visíveis
        blocos.forEach(bloco => {
            bloco.style.display = 'block';
        });
    }
    
    // Se não houver blocos, exibir mensagem de erro
    if (blocos.length === 0) {
        console.error("Nenhum bloco encontrado! Verificando a estrutura do DOM...");
        
        // Criar blocos manualmente se não existirem
        criarBlocosManualmente();
    }
}

// Função para criar blocos manualmente caso não sejam encontrados
function criarBlocosManualmente() {
    const container = document.querySelector('.user-check-container');
    
    if (!container) {
        console.error("Container de blocos não encontrado!");
        return;
    }
    
    console.log("Tentando criar blocos manualmente...");
    
    // Verificar se já existem blocos no container
    if (container.children.length > 0) {
        console.log("Container já possui filhos, não criando novos blocos.");
        return;
    }
    
    // Criar blocos padrão para testes
    const blocosPadrao = [
        { id: "Bloco_Padrao_1", nome: "Bloco Padrão 1", obrigatorio: true },
        { id: "Bloco_Padrao_2", nome: "Bloco Padrão 2", obrigatorio: false },
        { id: "Sumario_Executivo", nome: "Sumário Executivo", obrigatorio: true },
        { id: "Visao_Geral_dos_Servicos", nome: "Visão Geral dos Serviços", obrigatorio: true },
        { id: "Workplace_Field_Services", nome: "Workplace Field Services", obrigatorio: false }
    ];
    
    blocosPadrao.forEach(bloco => {
        const item = document.createElement('div');
        item.className = 'user-check-item';
        item.style.display = 'block';
        
        const formCheck = document.createElement('div');
        formCheck.className = 'form-check';
        
        const input = document.createElement('input');
        input.className = 'form-check-input';
        input.type = 'checkbox';
        input.id = `bloco_${bloco.id}`;
        input.name = 'blocos_permitidos';
        input.value = bloco.id;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `bloco_${bloco.id}`;
        label.textContent = bloco.nome;
        
        const small = document.createElement('div');
        small.innerHTML = `<small>${bloco.id}</small>`;
        
        if (bloco.obrigatorio) {
            const badge = document.createElement('span');
            badge.className = 'bloco-badge obrigatorio';
            badge.textContent = 'Obrigatório';
            small.appendChild(badge);
        }
        
        label.appendChild(small);
        formCheck.appendChild(input);
        formCheck.appendChild(label);
        item.appendChild(formCheck);
        container.appendChild(item);
    });
    
    console.log("Blocos criados manualmente:", blocosPadrao.length);
}

// Função para confirmar remoção
function confirmarRemocao(login) {
    document.getElementById('nomeUsuario').textContent = login;
    document.getElementById('remover_usuario').value = login;
    abrirModal('removerModal');
}

// Funções para modal
function abrirModal(id) {
    document.getElementById(id).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharModal(id) {
    document.getElementById(id).classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Seleção de perfil
function selecionarPerfil(element) {
    // Remover seleção atual
    document.querySelectorAll('.perfil-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Adicionar seleção ao elemento clicado
    element.classList.add('selected');
    
    // Atualizar o valor do campo hidden
    document.getElementById('perfil').value = element.getAttribute('data-value');
}

// Funções para gerenciar seleção de blocos
function toggleBlocosAcesso(tipo) {
    console.log("Tipo de acesso selecionado:", tipo);
    const blocosSelecao = document.getElementById('blocos-selecao');
    
    if (tipo === 'especificos') {
        blocosSelecao.style.display = 'block';
        
        // Verificar blocos disponíveis
        verificarBlocos();
        
        // Verificar se o elemento de pesquisa de blocos já existe
        if (!document.getElementById('pesquisar-bloco')) {
            const searchContainer = document.createElement('div');
            searchContainer.className = 'search-container mb-3';
            
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.id = 'pesquisar-bloco';
            searchInput.className = 'search-input';
            searchInput.placeholder = 'Pesquisar blocos...';
            
            searchContainer.appendChild(searchInput);
            blocosSelecao.insertBefore(searchContainer, blocosSelecao.firstChild);
            
            // Adicionar evento de pesquisa
            searchInput.addEventListener('input', function() {
                const termo = this.value.toLowerCase();
                
                const blocos = document.querySelectorAll('.user-check-item');
                blocos.forEach(bloco => {
                    const label = bloco.querySelector('label').textContent.toLowerCase();
                    
                    if (label.includes(termo)) {
                        bloco.style.display = 'block';
                    } else {
                        bloco.style.display = 'none';
                    }
                });
            });
        }
    } else {
        blocosSelecao.style.display = 'none';
    }
}

function selecionarTodosBlocos(selecionar) {
    const checkboxes = document.querySelectorAll('input[name="blocos_permitidos"]');
    console.log("Total de checkboxes encontrados:", checkboxes.length);
    
    checkboxes.forEach(checkbox => {
        // Apenas selecionar os blocos que estão visíveis
        if (checkbox.closest('.user-check-item').style.display != 'none') {
            checkbox.checked = selecionar;
        }
    });
} 