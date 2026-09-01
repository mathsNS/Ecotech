document.querySelectorAll('[data-address-form]').forEach(form => {
    const cep = form.querySelector('.cep-input');
    const status = form.querySelector('.address-status');
    if (!cep) return;

    cep.addEventListener('input', () => {
        const digits = cep.value.replace(/\D/g, '').slice(0, 8);
        cep.value = digits.replace(/(\d{5})(\d)/, '$1-$2');
    });

    cep.addEventListener('blur', async () => {
        const digits = cep.value.replace(/\D/g, '');
        if (!digits) return;
        if (digits.length !== 8) {
            status.textContent = 'Digite um CEP válido com 8 números.';
            status.className = 'address-status error';
            return;
        }
        status.textContent = 'Buscando endereço…';
        status.className = 'address-status loading';
        try {
            const response = await fetch(`/api/cep/${digits}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.erro || 'CEP não encontrado');
            const assign = (selector, value) => {
                const field = form.querySelector(selector);
                if (field && value) field.value = value;
            };
            assign('.street-input', data.street);
            assign('.neighborhood-input', data.neighborhood);
            assign('.city-input', data.city);
            assign('.state-input', data.state);
            assign('[name="latitude"], [name="latitude_coleta"]', data.latitude);
            assign('[name="longitude"], [name="longitude_coleta"]', data.longitude);
            status.textContent = 'Endereço localizado. Confira os dados e informe o número.';
            status.className = 'address-status success';
        } catch (error) {
            status.textContent = error.message;
            status.className = 'address-status error';
        }
    });
});
