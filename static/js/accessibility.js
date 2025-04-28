/**
 * Melhorias de acessibilidade - Proposal Creator
 * 
 * Este script implementa recursos de acessibilidade para melhorar a experiência do usuário,
 * incluindo controle de zoom e navegação por teclado.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuração inicial
    const body = document.body;
    let currentZoom = parseFloat(localStorage.getItem('userZoom')) || 1;
    
    // Aplicar zoom salvo anteriormente
    applyZoom(currentZoom);
    
    // Botões de acessibilidade - Zoom
    const zoomInBtn = document.getElementById('zoom-in');
    const zoomOutBtn = document.getElementById('zoom-out');
    const zoomResetBtn = document.getElementById('zoom-reset');
    
    if (zoomInBtn && zoomOutBtn && zoomResetBtn) {
        zoomInBtn.addEventListener('click', function() {
            if (currentZoom < 1.5) {
                currentZoom += 0.1;
                applyZoom(currentZoom);
            }
        });
        
        zoomOutBtn.addEventListener('click', function() {
            if (currentZoom > 0.8) {
                currentZoom -= 0.1;
                applyZoom(currentZoom);
            }
        });
        
        zoomResetBtn.addEventListener('click', function() {
            currentZoom = 1;
            applyZoom(currentZoom);
        });
    }
    
    // Atalhos de teclado para acessibilidade
    document.addEventListener('keydown', function(e) {
        // Alt + z para aumentar zoom
        if (e.altKey && e.key === 'z') {
            if (currentZoom < 1.5) {
                currentZoom += 0.1;
                applyZoom(currentZoom);
            }
            e.preventDefault();
        }
        
        // Alt + x para diminuir zoom
        if (e.altKey && e.key === 'x') {
            if (currentZoom > 0.8) {
                currentZoom -= 0.1;
                applyZoom(currentZoom);
            }
            e.preventDefault();
        }
        
        // Alt + c para reset zoom
        if (e.altKey && e.key === 'c') {
            currentZoom = 1;
            applyZoom(currentZoom);
            e.preventDefault();
        }
        
        // Alt + m para ir para o menu
        if (e.altKey && e.key === 'm') {
            const firstMenuItem = document.querySelector('.menu-link');
            if (firstMenuItem) {
                firstMenuItem.focus();
                e.preventDefault();
            }
        }
        
        // Alt + s para ir para o conteúdo principal
        if (e.altKey && e.key === 's') {
            const mainContent = document.getElementById('main-content');
            if (mainContent) {
                mainContent.focus();
                e.preventDefault();
            }
        }
    });
    
    // Funções de acessibilidade
    function applyZoom(zoomLevel) {
        document.documentElement.style.setProperty('--user-zoom', zoomLevel);
        body.classList.add('font-size-control');
        localStorage.setItem('userZoom', zoomLevel.toString());
        
        // Ajustar elementos específicos para melhor visualização com zoom
        adjustZoomSpecificElements(zoomLevel);
    }
    
    function adjustZoomSpecificElements(zoomLevel) {
        // Ajustar tamanho de elementos específicos com base no zoom
        if (zoomLevel > 1.2) {
            // Para zoom alto, simplificar alguns componentes da interface
            document.querySelectorAll('.card').forEach(card => {
                card.classList.add('zoom-adjusted');
            });
            
            document.querySelectorAll('table').forEach(table => {
                table.classList.add('zoom-adjusted');
            });
        } else {
            // Remover ajustes para zoom normal
            document.querySelectorAll('.card, table').forEach(el => {
                el.classList.remove('zoom-adjusted');
            });
        }
    }
    
    function notifyAccessibilityChange(message) {
        // Criar uma notificação temporária para mudanças de acessibilidade
        const notification = document.createElement('div');
        notification.className = 'accessibility-notification';
        notification.setAttribute('role', 'status');
        notification.setAttribute('aria-live', 'polite');
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remover após 3 segundos
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }
    
    // Adicionar classes para tabelas para melhor acessibilidade
    document.querySelectorAll('table').forEach(table => {
        table.classList.add('table-responsive');
        
        // Se não tiver um caption, adicionar um para leitores de tela
        if (!table.querySelector('caption')) {
            const tableParent = table.parentElement;
            const previousHeading = 
                tableParent.previousElementSibling && 
                tableParent.previousElementSibling.tagName.match(/H[1-6]/) ? 
                tableParent.previousElementSibling.textContent.trim() : 
                'Tabela de dados';
                
            const caption = document.createElement('caption');
            caption.className = 'sr-only'; // Visível apenas para leitores de tela
            caption.textContent = previousHeading;
            table.prepend(caption);
        }
    });
    
    // Melhorar a acessibilidade de formulários
    document.querySelectorAll('input, select, textarea').forEach(field => {
        // Se o campo não tem um ID, criar um
        if (!field.id) {
            const randomId = 'field-' + Math.random().toString(36).substring(2, 9);
            field.id = randomId;
            
            // Procurar por um label associado e atualizá-lo
            const parentLabel = field.closest('label');
            if (parentLabel) {
                parentLabel.htmlFor = randomId;
            }
        }
        
        // Adicionar atributos ARIA para validação de formulários
        field.addEventListener('invalid', function() {
            this.setAttribute('aria-invalid', 'true');
            
            // Criar uma mensagem de erro se não existir
            let errorId = this.id + '-error';
            let errorElement = document.getElementById(errorId);
            
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.id = errorId;
                errorElement.className = 'error-message';
                errorElement.setAttribute('aria-live', 'polite');
                this.parentNode.appendChild(errorElement);
                
                // Associar a mensagem de erro ao campo
                this.setAttribute('aria-describedby', errorId);
            }
            
            errorElement.textContent = this.validationMessage;
        });
        
        // Limpar estado de erro quando o campo é corrigido
        field.addEventListener('input', function() {
            if (this.getAttribute('aria-invalid') === 'true') {
                this.removeAttribute('aria-invalid');
                
                const errorId = this.id + '-error';
                const errorElement = document.getElementById(errorId);
                if (errorElement) {
                    errorElement.textContent = '';
                }
            }
        });
    });

    // Adicionar CSS para notificações de acessibilidade
    const style = document.createElement('style');
    style.textContent = `
        .accessibility-notification {
            position: fixed;
            bottom: 100px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 1000;
            animation: fadeIn 0.3s ease;
        }
        
        .accessibility-notification.fade-out {
            animation: fadeOut 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(20px); }
        }
        
        /* Estilos para tabelas com zoom ajustado */
        .zoom-adjusted {
            font-size: 0.9em;
        }
    `;
    document.head.appendChild(style);
});