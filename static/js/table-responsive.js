/**
 * Melhorias para tabelas responsivas - Proposal Creator
 * 
 * Este script melhora a experiência do usuário com tabelas em dispositivos móveis,
 * adicionando rótulos e outros recursos interativos.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Identificar todas as tabelas na página
    const tables = document.querySelectorAll('table:not(.responsive-table)');
    
    // Para cada tabela, verificar se precisa de tratamento responsivo
    tables.forEach(function(table) {
        // Verificar primeiro se a tabela já é configurada como responsiva
        if (table.classList.contains('responsive-table')) {
            return;
        }
        
        // Primeiro, adicionar a classe de tabela responsiva
        table.classList.add('responsive-table');
        
        // Verificar se tem container ou criar um
        let tableContainer = table.parentElement;
        if (!tableContainer.classList.contains('table-container')) {
            // Envolver a tabela em um container
            tableContainer = document.createElement('div');
            tableContainer.className = 'table-container';
            table.parentNode.insertBefore(tableContainer, table);
            tableContainer.appendChild(table);
        }
        
        // Obter cabeçalhos da tabela
        const headers = Array.from(table.querySelectorAll('thead th'))
            .map(th => th.textContent.trim());
        
        // Se não tiver cabeçalhos, buscar na primeira linha
        if (headers.length === 0) {
            const firstRow = table.querySelector('tr');
            if (firstRow) {
                const firstRowCells = firstRow.querySelectorAll('th, td');
                Array.from(firstRowCells).forEach(cell => {
                    headers.push(cell.textContent.trim());
                });
                
                // Se os cabeçalhos estiverem na primeira linha e não em um thead,
                // considerar adicioná-los a um thead criado dinamicamente
                if (headers.length > 0 && !table.querySelector('thead')) {
                    const thead = document.createElement('thead');
                    thead.appendChild(firstRow.cloneNode(true));
                    table.insertBefore(thead, table.firstChild);
                }
            }
        }
        
        // Adicionar atributos data para rótulos em visualização móvel
        if (headers.length > 0) {
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
        
        // Identificar células de ações (células com botões ou links)
        const actionCells = table.querySelectorAll('td:has(button), td:has(a.btn)');
        actionCells.forEach(cell => {
            cell.classList.add('actions');
        });
        
        // Verificar se a tabela precisa de indicador de rolagem
        const checkTableScroll = function() {
            if (tableContainer.scrollWidth > tableContainer.clientWidth) {
                tableContainer.classList.add('scrollable');
            } else {
                tableContainer.classList.remove('scrollable');
            }
        };
        
        // Verificar inicialmente
        checkTableScroll();
        
        // Adicionar verificação em eventos de redimensionamento
        window.addEventListener('resize', checkTableScroll);
    });
    
    // Tornar linhas de tabela clicáveis se tiverem links
    const clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(row => {
        row.classList.add('clickable');
        row.addEventListener('click', function() {
            window.location.href = this.dataset.href;
        });
        
        // Acessibilidade para navegação por teclado
        row.setAttribute('tabindex', '0');
        row.addEventListener('keydown', function(e) {
            // Navegar com Enter ou Space
            if (e.key === 'Enter' || e.key === ' ') {
                window.location.href = this.dataset.href;
                e.preventDefault();
            }
        });
    });
    
    // Adicionar botão de expansão para tabelas grandes em dispositivos móveis
    if (window.innerWidth <= 768) {
        const largeTables = document.querySelectorAll('.table-container:has(table)');
        largeTables.forEach(container => {
            const table = container.querySelector('table');
            if (table && table.offsetWidth > container.offsetWidth) {
                container.classList.add('js-responsive-table');
                
                const expandButton = document.createElement('button');
                expandButton.className = 'expand-button';
                expandButton.innerHTML = '<i class="fas fa-expand-alt"></i>';
                expandButton.setAttribute('aria-label', 'Expandir tabela');
                expandButton.setAttribute('title', 'Expandir para visualizar toda a tabela');
                
                container.appendChild(expandButton);
                
                expandButton.addEventListener('click', function() {
                    container.classList.toggle('expanded');
                    this.innerHTML = container.classList.contains('expanded') 
                        ? '<i class="fas fa-compress-alt"></i>' 
                        : '<i class="fas fa-expand-alt"></i>';
                    
                    this.setAttribute('aria-label', 
                        container.classList.contains('expanded') 
                            ? 'Comprimir tabela' 
                            : 'Expandir tabela'
                    );
                });
            }
        });
    }
}); 