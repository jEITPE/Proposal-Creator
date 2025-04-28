// JavaScript para gerenciamento de ofertas
document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const blocosCheckboxes = document.querySelectorAll('.bloco-checkbox');
    const blocosObrigatoriosContainer = document.getElementById('blocos-obrigatorios-container');
    const pesquisarBlocos = document.getElementById('pesquisar-blocos');
    const editButtons = document.querySelectorAll('.edit-oferta-btn');
    const deleteButtons = document.querySelectorAll('.delete-oferta-btn');
    const selecionarTodosBtn = document.getElementById('selecionar-todos-blocos');
    const deselecionarTodosBtn = document.getElementById('deselecionar-todos-blocos');
    const ofertaForm = document.getElementById('ofertaForm');
    const ofertaCards = document.querySelectorAll('.oferta-card');
    
    // ========================
    // Funções principais
    // ========================
    
    /**
     * Atualiza a lista de blocos obrigatórios com base nos blocos selecionados
     */
    function updateObrigatoriosList() {
        const selectedBlocks = [];
        blocosCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selectedBlocks.push({
                    nome: checkbox.value,
                    id: checkbox.id
                });
            }
        });
        
        if (selectedBlocks.length > 0) {
            let html = '';
            selectedBlocks.forEach(block => {
                html += `
                <div class="bloco-checkbox-container">
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="obrigatorio_${block.nome}" 
                               name="blocos_obrigatorios" value="${block.nome}">
                        <label class="custom-control-label" for="obrigatorio_${block.nome}">${block.nome}</label>
                    </div>
                </div>`;
            });
            blocosObrigatoriosContainer.innerHTML = html;
            
            // Animar os elementos recém-adicionados para melhor feedback visual
            const items = blocosObrigatoriosContainer.querySelectorAll('.bloco-checkbox-container');
            items.forEach((item, index) => {
                item.style.opacity = 0;
                item.style.transform = 'translateY(10px)';
                
                setTimeout(() => {
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = 1;
                    item.style.transform = 'translateY(0)';
                }, 50 * index);
            });
        } else {
            blocosObrigatoriosContainer.innerHTML = '<p class="text-muted text-center py-3">Selecione blocos acima para configurar como obrigatórios</p>';
        }
    }
    
    /**
     * Configura o modal para edição de uma oferta existente
     * @param {Object} data - Dados da oferta a ser editada
     */
    function setupEditModal(data) {
        const { tipo, descricao, blocos, obrigatorios } = data;

        console.log('Configurando modal para edição - dados recebidos:', data);

        // Preencher o formulário
        document.getElementById('acao').value = 'editar';
        document.getElementById('tipo_oferta').value = tipo;
        document.getElementById('tipo_oferta').readOnly = true;
        document.getElementById('descricao').value = descricao || '';
        
        // Limpar checkboxes
        blocosCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Marcar blocos selecionados - corrigido para lidar com formato de objeto ou array
        let blocosList = [];
        if (Array.isArray(blocos)) {
            blocosList = blocos;
        } else if (typeof blocos === 'object') {
            blocosList = Object.keys(blocos);
        }
        
        console.log('Blocos a serem marcados:', blocosList);
        
        blocosList.forEach(bloco => {
            const checkbox = document.getElementById(`bloco_${bloco}`);
            if (checkbox) {
                checkbox.checked = true;
                console.log(`Checkbox marcado: bloco_${bloco}`);
            } else {
                console.warn(`Checkbox não encontrado: bloco_${bloco}`);
            }
        });
        
        // Atualizar lista de obrigatórios e marcar os obrigatórios
        updateObrigatoriosList();
        
        setTimeout(() => {
            let obrigatoriosList = Array.isArray(obrigatorios) ? obrigatorios : [];
            console.log('Blocos obrigatórios a serem marcados:', obrigatoriosList);
            
            obrigatoriosList.forEach(obrigatorio => {
                const checkbox = document.getElementById(`obrigatorio_${obrigatorio}`);
                if (checkbox) {
                    checkbox.checked = true;
                    console.log(`Checkbox obrigatório marcado: obrigatorio_${obrigatorio}`);
                } else {
                    console.warn(`Checkbox obrigatório não encontrado: obrigatorio_${obrigatorio}`);
                }
            });
        }, 150);
        
        // Atualizar título do modal
        document.getElementById('addOfertaModalLabel').textContent = 'Editar Oferta';
        
        // Abrir modal com animação suave
        const modal = $('#addOfertaModal');
        modal.modal('show');
        setTimeout(() => {
            const modalContent = modal.find('.modal-content');
            modalContent.css('transform', 'translateY(0)');
            modalContent.css('opacity', '1');
        }, 150);
    }
    
    /**
     * Reinicia o modal para o estado inicial após ser fechado
     */
    function resetModal() {
        document.getElementById('ofertaForm').reset();
        document.getElementById('acao').value = 'adicionar';
        document.getElementById('tipo_oferta').readOnly = false;
        document.getElementById('addOfertaModalLabel').textContent = 'Nova Oferta';
        
        // Limpar a pesquisa
        if (pesquisarBlocos) {
            pesquisarBlocos.value = '';
            const blocos = document.querySelectorAll('.bloco-checkbox-container');
            blocos.forEach(bloco => {
                bloco.style.display = 'block';
            });
        }
        
        updateObrigatoriosList();
    }
    
    /**
     * Filtra os blocos com base no termo de pesquisa
     * @param {string} termo - Termo de pesquisa
     */
    function filtrarBlocos(termo) {
        const termoBusca = termo.toLowerCase();
        const blocos = document.querySelectorAll('.bloco-checkbox-container');
        let encontrados = 0;
        
        blocos.forEach(bloco => {
            const label = bloco.querySelector('label');
            if (!label) return;
            
            const nome = label.textContent.toLowerCase();
            
            if (nome.includes(termoBusca)) {
                bloco.style.display = 'block';
                bloco.style.order = nome.indexOf(termoBusca); // Ordenar resultados por relevância
                encontrados++;
                
                // Destacar o termo pesquisado
                if (termoBusca.length > 0) {
                    const textoOriginal = label.textContent;
                    const regex = new RegExp(`(${escapeRegExp(termoBusca)})`, 'gi');
                    const textoDestacado = textoOriginal.replace(regex, '<mark>$1</mark>');
                    label.innerHTML = textoDestacado;
                }
            } else {
                bloco.style.display = 'none';
            }
        });
        
        // Feedback quando não encontrar resultados
        const blocosSeletor = document.querySelector('.blocos-selector');
        const mensagemNaoEncontrado = blocosSeletor.querySelector('.sem-resultados');
        
        if (encontrados === 0 && termoBusca.length > 0) {
            if (!mensagemNaoEncontrado) {
                const mensagem = document.createElement('p');
                mensagem.className = 'text-center text-muted py-3 sem-resultados';
                mensagem.innerHTML = `Nenhum bloco encontrado para "<strong>${termo}</strong>"`;
                blocosSeletor.appendChild(mensagem);
            }
        } else if (mensagemNaoEncontrado) {
            mensagemNaoEncontrado.remove();
        }
    }
    
    // Função auxiliar para escapar caracteres especiais em regex
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    /**
     * Valida o formulário antes do envio
     * @returns {boolean} - Indica se o formulário é válido
     */
    function validarFormulario() {
        const tipoOferta = document.getElementById('tipo_oferta').value.trim();
        const blocosChecked = Array.from(blocosCheckboxes).some(checkbox => checkbox.checked);
        
        let isValid = true;
        let message = '';
        
        if (!tipoOferta) {
            message = 'Por favor, informe o nome da oferta.';
            isValid = false;
        } else if (!blocosChecked) {
            message = 'Selecione pelo menos um bloco para esta oferta.';
            isValid = false;
        }
        
        if (!isValid) {
            // Mostrar feedback ao usuário
            const alertExistente = document.querySelector('.alert-validation');
            if (alertExistente) alertExistente.remove();
            
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-validation mb-3';
            alert.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i> ${message}`;
            
            const modalBody = document.querySelector('.modal-body');
            modalBody.insertBefore(alert, modalBody.firstChild);
            
            // Animar o alerta
            alert.style.opacity = 0;
            alert.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                alert.style.transition = 'all 0.3s ease';
                alert.style.opacity = 1;
                alert.style.transform = 'translateY(0)';
            }, 10);
            
            return false;
        }
        
        return true;
    }

    /**
     * Mostra uma mensagem de toast para o usuário
     * @param {string} mensagem - A mensagem a ser exibida
     * @param {string} tipo - O tipo de mensagem (success, error, warning, info)
     */
    function mostrarToast(mensagem, tipo = 'success') {
        // Verificar se o container de toasts existe
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 right-0 p-3';
            toastContainer.style.zIndex = '5';
            toastContainer.style.right = '0';
            toastContainer.style.bottom = '0';
            document.body.appendChild(toastContainer);
        }
        
        // Criar o toast
        const toastId = `toast-${Date.now()}`;
        const toast = document.createElement('div');
        toast.className = `toast bg-${tipo === 'error' ? 'danger' : tipo}`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.style.minWidth = '250px';
        
        // Conteúdo do toast
        let iconClass = 'fa-check-circle';
        if (tipo === 'error') iconClass = 'fa-times-circle';
        if (tipo === 'warning') iconClass = 'fa-exclamation-triangle';
        if (tipo === 'info') iconClass = 'fa-info-circle';
        
        toast.innerHTML = `
            <div class="toast-header bg-${tipo === 'error' ? 'danger' : tipo} text-white">
                <i class="fas ${iconClass} mr-2"></i>
                <strong class="mr-auto">${tipo === 'error' ? 'Erro' : tipo === 'warning' ? 'Atenção' : tipo === 'info' ? 'Informação' : 'Sucesso'}</strong>
                <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Fechar">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="toast-body text-${tipo === 'error' ? 'white' : tipo === 'success' ? 'white' : 'dark'}">
                ${mensagem}
            </div>
        `;
        
        // Adicionar o toast ao container
        toastContainer.appendChild(toast);
        
        // Inicializar e mostrar o toast usando jQuery
        $(`#${toastId}`).toast({
            delay: 5000,
            autohide: true
        });
        $(`#${toastId}`).toast('show');
        
        // Remover o toast após fechar
        $(`#${toastId}`).on('hidden.bs.toast', function() {
            this.remove();
        });
    }

    /**
     * Salva uma oferta usando a API
     * @param {Object} dados - Dados da oferta a serem salvos
     * @param {Function} callback - Função de callback após salvar
     */
    function salvarOfertaViaAPI(dados, callback) {
        // Mostrar loader
        const btnSubmit = document.querySelector('#ofertaForm button[type="submit"]');
        const btnText = btnSubmit.innerHTML;
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        console.log('Enviando requisição para /api/salvar_oferta');
        
        fetch('/api/salvar_oferta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(dados)
        })
        .then(response => {
            console.log('Resposta recebida:', response.status);
            return response.json();
        })
        .then(data => {
            // Restaurar botão
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = btnText;
            
            console.log('Dados recebidos após salvar:', data);
            
            if (data.erro) {
                console.error('Erro retornado pelo servidor:', data.erro);
                mostrarToast(data.erro, 'error');
                return;
            }
            
            // Mostrar mensagem de sucesso
            mostrarToast(data.sucesso, 'success');
            
            // Fechar modal
            $('#addOfertaModal').modal('hide');
            
            // Executar callback (normalmente recarregar página)
            if (typeof callback === 'function') {
                callback();
            }
        })
        .catch(error => {
            console.error('Erro ao salvar oferta:', error);
            mostrarToast('Erro ao salvar oferta. Tente novamente.', 'error');
            
            // Restaurar botão
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = btnText;
        });
    }

    /**
     * Carrega os detalhes de uma oferta via API
     * @param {string} tipoOferta - O tipo da oferta a ser carregada
     * @param {Function} callback - Função a ser chamada com os dados carregados
     */
    function carregarOfertaViaAPI(tipoOferta, callback) {
        console.log(`Carregando oferta: ${tipoOferta}`);
        
        // Mostrar indicação de carregamento na tela
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay animate-fade-in';
        loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="sr-only">Carregando...</span></div>';
        document.body.appendChild(loadingOverlay);
        
        fetch(`/api/oferta/${encodeURIComponent(tipoOferta)}`)
            .then(response => {
                console.log(`Resposta recebida para ${tipoOferta}:`, response.status);
                if (!response.ok) {
                    throw new Error(`Status HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`Dados recebidos para ${tipoOferta}:`, data);
                
                // Remover overlay
                document.body.removeChild(loadingOverlay);
                
                if (data.erro) {
                    mostrarToast(data.erro, 'error');
                    return;
                }
                
                if (typeof callback === 'function') {
                    callback(data);
                }
            })
            .catch(error => {
                console.error('Erro ao carregar detalhes da oferta:', error);
                
                // Remover overlay
                if (document.body.contains(loadingOverlay)) {
                    document.body.removeChild(loadingOverlay);
                }
                
                mostrarToast('Erro ao carregar detalhes da oferta. Tente novamente.', 'error');
                
                // Mostrar erro no card da oferta
                const erroContainer = document.getElementById(`erro-oferta-${tipoOferta.replace(/ /g, '_')}`);
                if (erroContainer) {
                    const mensagemSpan = erroContainer.querySelector('.mensagem-erro');
                    if (mensagemSpan) {
                        mensagemSpan.textContent = `Erro ao carregar detalhes: ${error.message}`;
                    }
                    erroContainer.style.display = 'block';
                    
                    // Restaurar botão para estado original
                    const editButton = document.querySelector(`.edit-oferta-btn[data-tipo="${tipoOferta}"]`);
                    if (editButton) {
                        editButton.innerHTML = '<i class="fas fa-edit"></i> Editar';
                        editButton.disabled = false;
                    }
                }
                
                // Permitir usar os dados do botão como fallback
                if (typeof callback === 'function') {
                    const fallbackData = obterDadosFallback(tipoOferta);
                    if (fallbackData) {
                        console.log('Usando dados de fallback:', fallbackData);
                        callback(fallbackData);
                    }
                }
            });
    }
    
    /**
     * Obtém dados de fallback do botão de edição para o caso da API falhar
     * @param {string} tipoOferta - O tipo da oferta
     * @returns {Object|null} - Dados de fallback ou null se não encontrados
     */
    function obterDadosFallback(tipoOferta) {
        const editButton = document.querySelector(`.edit-oferta-btn[data-tipo="${tipoOferta}"]`);
        if (!editButton) return null;
        
        try {
            const descricao = editButton.getAttribute('data-descricao') || '';
            let blocos = [];
            let obrigatorios = [];
            
            try {
                const blocosRaw = editButton.getAttribute('data-blocos');
                const obrigatoriosRaw = editButton.getAttribute('data-obrigatorios');
                
                if (blocosRaw) {
                    const blocosParsed = JSON.parse(blocosRaw);
                    if (typeof blocosParsed === 'object') {
                        blocos = Object.keys(blocosParsed);
                    } else if (Array.isArray(blocosParsed)) {
                        blocos = blocosParsed;
                    }
                }
                
                if (obrigatoriosRaw) {
                    obrigatorios = JSON.parse(obrigatoriosRaw);
                }
            } catch (e) {
                console.error('Erro ao parsear dados JSON do fallback:', e);
            }
            
            return {
                descricao,
                blocos,
                obrigatorios
            };
        } catch (e) {
            console.error('Erro ao obter dados de fallback:', e);
            return null;
        }
    }
    
    /**
     * Verifica o status da API antes de prosseguir com ações
     * @param {Function} callback - Função a ser executada se o status estiver ok
     */
    function verificarStatusAPI(callback) {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                console.log('Status da API:', data);
                if (data.status === 'online') {
                    if (typeof callback === 'function') {
                        callback();
                    }
                } else {
                    mostrarToast('A API está offline ou com problemas. Tente novamente mais tarde.', 'warning');
                }
            })
            .catch(error => {
                console.error('Erro ao verificar status da API:', error);
                mostrarToast('Não foi possível verificar o status da API. Verifique sua conexão.', 'error');
            });
    }
    
    // ========================
    // Event Listeners
    // ========================
    
    // Atualizar blocos obrigatórios quando blocos são selecionados/deselecionados
    blocosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Efeito visual ao selecionar
            const container = this.closest('.bloco-checkbox-container');
            if (this.checked) {
                container.style.backgroundColor = 'rgba(230, 0, 0, 0.05)';
                container.style.borderColor = 'rgba(230, 0, 0, 0.1)';
            } else {
                container.style.backgroundColor = '';
                container.style.borderColor = '';
            }
            
            updateObrigatoriosList();
        });
    });
    
    // Configurar botões de edição
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tipo = this.getAttribute('data-tipo');
            
            // Mostrar um indicador de carregamento no botão
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.disabled = true;
            
            // Verificar status da API antes de prosseguir
            verificarStatusAPI(() => {
                // Carregar dados atualizados da oferta via API
                carregarOfertaViaAPI(tipo, function(ofertaData) {
                    // Preparar dados para o modal
                    const dados = {
                        tipo: tipo,
                        descricao: ofertaData.descricao || '',
                        blocos: ofertaData.blocos || {},
                        obrigatorios: ofertaData.obrigatorios || []
                    };
                    
                    // Configurar e abrir o modal
                    setupEditModal(dados);
                    
                    // Restaurar estado original do botão
                    button.innerHTML = originalText;
                    button.disabled = false;
                });
            });
        });
    });
    
    // Pesquisa de blocos
    if (pesquisarBlocos) {
        pesquisarBlocos.addEventListener('input', function() {
            filtrarBlocos(this.value);
        });
        
        // Limpar pesquisa ao clicar no X
        const limparPesquisa = document.createElement('button');
        limparPesquisa.type = 'button';
        limparPesquisa.className = 'btn btn-sm btn-link position-absolute';
        limparPesquisa.innerHTML = '<i class="fas fa-times"></i>';
        limparPesquisa.style.right = '10px';
        limparPesquisa.style.top = '50%';
        limparPesquisa.style.transform = 'translateY(-50%)';
        limparPesquisa.style.display = 'none';
        
        pesquisarBlocos.parentNode.appendChild(limparPesquisa);
        
        pesquisarBlocos.addEventListener('input', function() {
            limparPesquisa.style.display = this.value ? 'block' : 'none';
        });
        
        limparPesquisa.addEventListener('click', function() {
            pesquisarBlocos.value = '';
            filtrarBlocos('');
            this.style.display = 'none';
            pesquisarBlocos.focus();
        });
    }
    
    // Configurar botões de exclusão
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tipo = this.getAttribute('data-tipo');
            document.getElementById('delete_tipo_oferta').value = tipo;
            document.getElementById('delete_oferta_nome').textContent = tipo;
            $('#deleteOfertaModal').modal('show');
        });
    });
    
    // Selecionar/deselecionar todos os blocos
    if (selecionarTodosBtn) {
        selecionarTodosBtn.addEventListener('click', function() {
            blocosCheckboxes.forEach(checkbox => {
                const container = checkbox.closest('.bloco-checkbox-container');
                if (container.style.display !== 'none') {
                    checkbox.checked = true;
                    container.style.backgroundColor = 'rgba(230, 0, 0, 0.05)';
                    container.style.borderColor = 'rgba(230, 0, 0, 0.1)';
                }
            });
            updateObrigatoriosList();
        });
    }
    
    if (deselecionarTodosBtn) {
        deselecionarTodosBtn.addEventListener('click', function() {
            blocosCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
                const container = checkbox.closest('.bloco-checkbox-container');
                container.style.backgroundColor = '';
                container.style.borderColor = '';
            });
            updateObrigatoriosList();
        });
    }
    
    // Submissão do formulário via API
    if (ofertaForm) {
        ofertaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Formulário de oferta submetido');
            
            if (!validarFormulario()) {
                console.error('Validação do formulário falhou');
                return false;
            }
            
            // Coletar dados do formulário
            const formData = new FormData(this);
            const dados = {
                acao: formData.get('acao'),
                tipo_oferta: formData.get('tipo_oferta'),
                descricao: formData.get('descricao'),
                blocos_selecionados: formData.getAll('blocos_selecionados'),
                blocos_obrigatorios: formData.getAll('blocos_obrigatorios')
            };
            
            console.log('Dados a serem enviados:', dados);
            
            // Mostrar mensagem de processamento
            mostrarToast('Enviando dados para o servidor...', 'info');
            
            // Salvar via API
            salvarOfertaViaAPI(dados, function() {
                // Recarregar a página para mostrar a oferta atualizada
                mostrarToast('Oferta salva com sucesso! Recarregando a página...', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 2000); // Aguardar 2 segundos para mostrar a mensagem
            });
            
            return false;
        });
    }
    
    // Submissão do formulário de exclusão via API
    const deleteOfertaForm = document.getElementById('deleteOfertaForm');
    if (deleteOfertaForm) {
        deleteOfertaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Coletar dados
            const tipoOferta = document.getElementById('delete_tipo_oferta').value;
            
            // Mostrar loader
            const btnSubmit = this.querySelector('button[type="submit"]');
            const btnText = btnSubmit.innerHTML;
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Excluindo...';
            
            // Enviar solicitação de exclusão
            fetch('/api/salvar_oferta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    acao: 'excluir',
                    tipo_oferta: tipoOferta
                })
            })
            .then(response => response.json())
            .then(data => {
                // Restaurar botão
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = btnText;
                
                if (data.erro) {
                    mostrarToast(data.erro, 'error');
                    return;
                }
                
                // Mostrar mensagem de sucesso
                mostrarToast(data.sucesso, 'success');
                
                // Fechar modal
                $('#deleteOfertaModal').modal('hide');
                
                // Recarregar a página
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                console.error('Erro ao excluir oferta:', error);
                mostrarToast('Erro ao excluir oferta. Tente novamente.', 'error');
                
                // Restaurar botão
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = btnText;
            });
            
            return false;
        });
    }
    
    // Reset modal quando fechado
    $('#addOfertaModal').on('hidden.bs.modal', resetModal);
    
    // Preparar o modal antes de mostrar
    $('#addOfertaModal').on('show.bs.modal', function() {
        const modalContent = $(this).find('.modal-content');
        modalContent.css('transform', 'translateY(-20px)');
        modalContent.css('opacity', '0');
        modalContent.css('transition', 'all 0.3s ease');
    });
    
    $('#addOfertaModal').on('shown.bs.modal', function() {
        const modalContent = $(this).find('.modal-content');
        modalContent.css('transform', 'translateY(0)');
        modalContent.css('opacity', '1');
        
        // Focar no primeiro campo
        document.getElementById('tipo_oferta').focus();
    });
    
    // Animações para cards de ofertas
    ofertaCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 15px 30px rgba(0,0,0,0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // Configurar botão de "Salvar via AJAX"
    const btnSalvarAjax = document.getElementById('salvar-via-ajax');
    if (btnSalvarAjax) {
        btnSalvarAjax.addEventListener('click', function() {
            console.log('Botão Salvar via AJAX clicado');
            
            // Exibir mensagem de status
            const statusMessage = document.getElementById('form-status-message');
            const statusText = document.getElementById('status-text');
            if (statusMessage && statusText) {
                statusMessage.style.display = 'block';
                statusMessage.className = 'alert alert-info';
                statusText.textContent = 'Coletando dados do formulário...';
            }
            
            // Coletar dados do formulário manualmente
            const acao = document.getElementById('acao').value;
            const tipoOferta = document.getElementById('tipo_oferta').value;
            const descricao = document.getElementById('descricao').value;
            
            // Coletar blocos selecionados
            const blocosSelecionados = [];
            document.querySelectorAll('.bloco-checkbox:checked').forEach(checkbox => {
                blocosSelecionados.push(checkbox.value);
            });
            
            // Coletar blocos obrigatórios
            const blocosObrigatorios = [];
            document.querySelectorAll('input[name="blocos_obrigatorios"]:checked').forEach(checkbox => {
                blocosObrigatorios.push(checkbox.value);
            });
            
            const dados = {
                acao: acao,
                tipo_oferta: tipoOferta,
                descricao: descricao,
                blocos_selecionados: blocosSelecionados,
                blocos_obrigatorios: blocosObrigatorios
            };
            
            console.log('Dados coletados manualmente:', dados);
            
            if (statusMessage && statusText) {
                statusText.textContent = 'Enviando dados para o servidor...';
            }
            
            // Enviar dados para o servidor
            fetch('/api/salvar_oferta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(dados)
            })
            .then(response => {
                console.log('Resposta do servidor:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Dados de resposta:', data);
                
                if (data.erro) {
                    console.error('Erro retornado pelo servidor:', data.erro);
                    if (statusMessage && statusText) {
                        statusMessage.className = 'alert alert-danger';
                        statusText.textContent = `Erro: ${data.erro}`;
                    }
                    mostrarToast(data.erro, 'error');
                } else {
                    if (statusMessage && statusText) {
                        statusMessage.className = 'alert alert-success';
                        statusText.textContent = data.sucesso || 'Operação realizada com sucesso!';
                    }
                    mostrarToast(data.sucesso, 'success');
                    
                    // Fechar modal e recarregar página após um tempo
                    setTimeout(() => {
                        $('#addOfertaModal').modal('hide');
                        window.location.reload();
                    }, 1500);
                }
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                if (statusMessage && statusText) {
                    statusMessage.className = 'alert alert-danger';
                    statusText.textContent = `Erro de conexão: ${error.message}`;
                }
                mostrarToast(`Erro de conexão: ${error.message}`, 'error');
            });
        });
    }
}); 