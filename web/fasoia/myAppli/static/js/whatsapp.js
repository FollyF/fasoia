// myAppli/static/myAppli/js/whatsapp.js

/**
 * Copie un texte dans le presse-papiers
 * @param {string} text - Le texte à copier
 */
function copyToClipboard(text) {
    // Utiliser l'API moderne du presse-papiers
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification('✅ Lien copié dans le presse-papiers !', 'success');
        }).catch(function(err) {
            console.error('Erreur de copie:', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        // Fallback pour les navigateurs plus anciens
        fallbackCopyToClipboard(text);
    }
}

/**
 * Méthode de secours pour la copie
 * @param {string} text 
 */
function fallbackCopyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showNotification('✅ Lien copié dans le presse-papiers !', 'success');
        } else {
            showNotification('❌ Erreur lors de la copie', 'error');
        }
    } catch (err) {
        console.error('Erreur fallback:', err);
        showNotification('❌ Impossible de copier', 'error');
    }
    
    document.body.removeChild(textarea);
}

/**
 * Affiche une notification temporaire
 * @param {string} message 
 * @param {string} type 
 */
function showNotification(message, type = 'info') {
    // Vérifier si une notification existe déjà
    let notification = document.getElementById('whatsapp-notification');
    
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'whatsapp-notification';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '15px 20px';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '9999';
        notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        notification.style.transition = 'opacity 0.3s';
        document.body.appendChild(notification);
    }
    
    // Style selon le type
    const colors = {
        success: { bg: '#d4edda', text: '#155724', border: '#c3e6cb' },
        error: { bg: '#f8d7da', text: '#721c24', border: '#f5c6cb' },
        warning: { bg: '#fff3cd', text: '#856404', border: '#ffeeba' },
        info: { bg: '#d1ecf1', text: '#0c5460', border: '#bee5eb' }
    };
    
    const color = colors[type] || colors.info;
    
    notification.style.backgroundColor = color.bg;
    notification.style.color = color.text;
    notification.style.border = `1px solid ${color.border}`;
    notification.innerHTML = message;
    notification.style.opacity = '1';
    
    // Disparaît après 3 secondes
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Copie tous les liens WhatsApp de la page
 */
function copyAllLinks() {
    const links = [];
    document.querySelectorAll('a[href^="https://wa.me"]').forEach(a => {
        links.push(a.href);
    });
    
    if (links.length > 0) {
        copyToClipboard(links.join('\n'));
        showNotification(`✅ ${links.length} liens copiés !`, 'success');
    } else {
        showNotification('❌ Aucun lien trouvé', 'warning');
    }
}

/**
 * Sélectionne/désélectionne toutes les entreprises
 * @param {boolean} check 
 */
function selectAll(check = true) {
    document.querySelectorAll('.entreprise-checkbox').forEach(cb => {
        cb.checked = check;
    });
}

/**
 * Ouvre WhatsApp avec un message pré-rempli
 * @param {string} url 
 */
function openWhatsApp(url) {
    window.open(url, '_blank');
    showNotification('📱 WhatsApp va s\'ouvrir...', 'info');
}

/**
 * Prépare un message pour plusieurs entreprises
 */
function prepareBulkSend() {
    const selected = [];
    document.querySelectorAll('.entreprise-checkbox:checked').forEach(cb => {
        selected.push(cb.value);
    });
    
    if (selected.length === 0) {
        showNotification('❌ Aucune entreprise sélectionnée', 'warning');
        return false;
    }
    
    showNotification(`📱 ${selected.length} entreprise(s) sélectionnée(s)`, 'success');
    return true;
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ WhatsApp JS chargé');
    
    // Ajouter des écouteurs d'événements si nécessaire
    const bulkSendBtn = document.getElementById('bulk-send-btn');
    if (bulkSendBtn) {
        bulkSendBtn.addEventListener('click', function(e) {
            if (!prepareBulkSend()) {
                e.preventDefault();
            }
        });
    }
});