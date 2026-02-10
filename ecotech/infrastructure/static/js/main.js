// JavaScript para funcionalidades adicionais, como auto-hide de alertas (apenas estetico)
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts após 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// toggle do bloco de doacoes
function toggleDonation() {
    const donationInfo = document.getElementById('donationInfo');
    if (donationInfo.style.display === 'none' || donationInfo.style.display === '') {
        donationInfo.style.display = 'block';
    } else {
        donationInfo.style.display = 'none';
    }
}

// Animação de slide out para alerts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
