/**
 * Responsividade aprimorada - Proposal Creator
 * 
 * Este script melhora a experiência do usuário em diferentes dispositivos
 * detectando características do dispositivo e ajustando o comportamento da interface.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Detecção de dispositivo e orientação
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent) || (window.innerWidth >= 768 && window.innerWidth <= 1024);
    const isLaptop = window.innerWidth > 1024 && window.innerWidth <= 1366;
    const isDesktop = window.innerWidth > 1366;
    
    // Adicionar classes ao body para CSS orientado a dispositivos
    const body = document.body;
    if (isMobile) body.classList.add('is-mobile');
    if (isTablet) body.classList.add('is-tablet');
    if (isLaptop) body.classList.add('is-laptop');
    if (isDesktop) body.classList.add('is-desktop');
    
    // Ajustes para dispositivos com tela sensível ao toque
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        body.classList.add('touch-device');
        
        // Aumentar área de toque para elementos interativos em dispositivos touch
        const touchTargets = document.querySelectorAll('.menu-link, .btn, .form-control, .card-header');
        touchTargets.forEach(element => {
            element.classList.add('touch-target');
        });
    }
    
    // Melhorar a experiência de rolagem
    if (isMobile || isTablet) {
        // Melhorar o comportamento de rolagem em dispositivos móveis
        document.querySelectorAll('.main-content, .sidebar, .block-list, .block-preview').forEach(el => {
            if (el) {
                el.style.WebkitOverflowScrolling = 'touch';
            }
        });
    }
    
    // Ajustes para o conteúdo da proposta em diferentes dispositivos
    const propostaContainer = document.querySelector('.proposal-container');
    if (propostaContainer) {
        if (isMobile) {
            adjustForMobileProposal();
        } else if (isTablet) {
            adjustForTabletProposal();
        } else if (isLaptop) {
            adjustForLaptopProposal();
        }
    }
    
    // Ajustes para gerenciamento de blocos em diferentes dispositivos
    const blocksManager = document.querySelector('.blocks-manager');
    if (blocksManager) {
        if (isMobile || isTablet) {
            adjustForMobileBlocks();
        }
    }
    
    // Lidar com orientação em dispositivos móveis
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Lidar com redimensionamento da janela
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(handleResize, 250);
    });
    
    // Funções de ajuste específicas para cada seção
    
    function adjustForMobileProposal() {
        // Ajustes para visualização de proposta em dispositivos móveis
        const blockSelectors = document.querySelectorAll('.block-selector');
        blockSelectors.forEach(selector => {
            selector.classList.add('mobile-layout');
        });
        
        // Simplificar a interface para melhor visualização em dispositivos móveis
        const advancedOptions = document.querySelectorAll('.advanced-options');
        advancedOptions.forEach(option => {
            const toggleButton = document.createElement('button');
            toggleButton.className = 'btn btn-sm btn-outline toggle-advanced';
            toggleButton.innerHTML = '<i class="fas fa-cog"></i> Opções Avançadas';
            toggleButton.addEventListener('click', function() {
                option.classList.toggle('show-options');
                this.innerHTML = option.classList.contains('show-options') 
                    ? '<i class="fas fa-times"></i> Fechar Opções' 
                    : '<i class="fas fa-cog"></i> Opções Avançadas';
            });
            
            option.classList.add('collapsible');
            option.parentNode.insertBefore(toggleButton, option);
        });
    }
    
    function adjustForTabletProposal() {
        // Ajustes para tablets
        const previewPanes = document.querySelectorAll('.preview-pane');
        previewPanes.forEach(pane => {
            pane.classList.add('tablet-optimized');
        });
    }
    
    function adjustForLaptopProposal() {
        // Otimizações para laptops
        const workspaceLayout = document.querySelector('.workspace-layout');
        if (workspaceLayout) {
            workspaceLayout.classList.add('laptop-optimized');
        }
    }
    
    function adjustForMobileBlocks() {
        // Otimizar gerenciamento de blocos para dispositivos menores
        const blockEditors = document.querySelectorAll('.block-editor');
        blockEditors.forEach(editor => {
            editor.classList.add('compact-layout');
            
            // Adicionar navegação simplificada para edição em dispositivos móveis
            const editorControls = editor.querySelector('.editor-controls');
            if (editorControls) {
                const mobileNav = document.createElement('div');
                mobileNav.className = 'mobile-editor-nav';
                mobileNav.innerHTML = `
                    <button class="btn btn-sm btn-outline mobile-nav-btn" data-target="editor">
                        <i class="fas fa-edit"></i> Editor
                    </button>
                    <button class="btn btn-sm btn-outline mobile-nav-btn" data-target="preview">
                        <i class="fas fa-eye"></i> Visualizar
                    </button>
                `;
                
                editorControls.parentNode.insertBefore(mobileNav, editorControls);
                
                // Adicionar comportamento para alternância de visualização
                mobileNav.querySelectorAll('.mobile-nav-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const target = this.getAttribute('data-target');
                        editor.setAttribute('data-active-view', target);
                        
                        // Atualizar botões ativos
                        mobileNav.querySelectorAll('.mobile-nav-btn').forEach(b => {
                            b.classList.remove('active');
                        });
                        this.classList.add('active');
                    });
                });
                
                // Ativar editor por padrão
                editor.setAttribute('data-active-view', 'editor');
                mobileNav.querySelector('[data-target="editor"]').classList.add('active');
            }
        });
    }
    
    function handleOrientationChange() {
        // Lidar com mudanças de orientação
        if (window.orientation === 90 || window.orientation === -90) {
            // Paisagem
            document.body.classList.add('landscape');
            document.body.classList.remove('portrait');
        } else {
            // Retrato
            document.body.classList.add('portrait');
            document.body.classList.remove('landscape');
        }
        
        // Re-aplicar ajustes para o novo tamanho de tela
        setTimeout(handleResize, 200);
    }
    
    function handleResize() {
        // Obter dimensões atuais da janela
        const width = window.innerWidth;
        
        // Atualizar classes do body com base no novo tamanho
        body.classList.remove('viewport-xs', 'viewport-sm', 'viewport-md', 'viewport-lg', 'viewport-xl');
        
        if (width <= 480) {
            body.classList.add('viewport-xs');
        } else if (width <= 768) {
            body.classList.add('viewport-sm');
        } else if (width <= 992) {
            body.classList.add('viewport-md');
        } else if (width <= 1200) {
            body.classList.add('viewport-lg');
        } else {
            body.classList.add('viewport-xl');
        }
        
        // Ajustar elementos específicos para o novo tamanho
        adjustTableResponsiveness();
    }
    
    function adjustTableResponsiveness() {
        // Tornar tabelas responsivas em dispositivos pequenos
        const tables = document.querySelectorAll('table:not(.responsive-table)');
        
        if (window.innerWidth <= 768) {
            tables.forEach(table => {
                if (!table.classList.contains('responsive-table')) {
                    table.classList.add('responsive-table');
                    
                    // Obter cabeçalhos da tabela
                    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
                    
                    // Adicionar atributos data para rótulos em visualização móvel
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        cells.forEach((cell, index) => {
                            if (headers[index]) {
                                cell.setAttribute('data-label', headers[index]);
                            }
                        });
                    });
                }
            });
        }
    }
}); 