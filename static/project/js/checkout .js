document.addEventListener('DOMContentLoaded', function () {
  const radios = document.querySelectorAll('input[name="payment_method"]');
  const btn = document.getElementById('submit-btn');

  function updateButton() {
    const selected = document.querySelector('input[name="payment_method"]:checked');
    if (selected && btn) {
      btn.innerText = selected.value === 'Online' ? 'Pay Now' : 'Place Order';
    }
  }

  radios.forEach(radio => {
    radio.addEventListener('change', updateButton);
  });

  updateButton();  
});
