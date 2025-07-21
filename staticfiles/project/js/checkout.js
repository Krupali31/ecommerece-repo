document.addEventListener('DOMContentLoaded', function () {
  const codRadio = document.querySelector('input[value="COD"]');
  const onlineRadio = document.querySelector('input[value="Online"]');
  const submitBtn = document.getElementById('submit-btn');

  if (!codRadio || !onlineRadio || !submitBtn) {
    console.warn("Required elements not found");
    return;
  }

  function updateButtonText() {
    submitBtn.innerText = onlineRadio.checked ? "💳 Pay Now" : "🛒 Place Order";
  }

  codRadio.addEventListener('change', updateButtonText);
  onlineRadio.addEventListener('change', updateButtonText);

  updateButtonText(); // Set default on load
});
