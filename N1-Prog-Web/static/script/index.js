// Adiciona o comportamento de pular para o próximo campo ao pressionar Enter
document.querySelectorAll('input').forEach((input, index, inputs) => {
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Previne o envio do formulário
            const nextInput = inputs[index + 1];
            if (nextInput) {
                nextInput.focus(); // Move o foco para o próximo input
            } else {
                // Se estiver no último input, submete o formulário
                this.form.submit();
            }
        }
    });
});
