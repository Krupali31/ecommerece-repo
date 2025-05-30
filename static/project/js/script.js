// Define the changeQty function globally, not inside DOMContentLoaded
function changeQty(button, delta) {
    const form = button.closest('form');  // Find the closest form
    const input = form.querySelector('.quantity-input');  // Get the input field
    let qty = parseInt(input.value) || 1;  // Get the current quantity, default to 1 if not a number
    qty = Math.max(1, qty + delta);  // Make sure the quantity doesn't go below 1
    input.value = qty;  // Update the input field value
    form.querySelector('.qty').innerText = qty;  // Update the quantity displayed next to the button
}

// This code will be executed when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Attach event listeners to the buttons for changing quantity
    const minusButtons = document.querySelectorAll('.btn-primary[onclick*="changeQty(this, -1)"]');
    const plusButtons = document.querySelectorAll('.btn-primary[onclick*="changeQty(this, 1)"]');
  
    minusButtons.forEach(button => {
      button.addEventListener('click', function() {
        changeQty(this, -1);  // Decrease quantity
      });
    });
  
    plusButtons.forEach(button => {
      button.addEventListener('click', function() {
        changeQty(this, 1);  // Increase quantity
      });
    });
  
    // Handle payment method change
    const paymentMethod = document.getElementById('payment-method');
    if (paymentMethod) {
      const upiDiv = document.getElementById('upi-div');
      const cardDiv = document.getElementById('card-div');
  
      paymentMethod.addEventListener('change', function () {
        upiDiv?.classList.add('d-none');
        cardDiv?.classList.add('d-none');
  
        if (this.value === 'UPI') {
          upiDiv?.classList.remove('d-none');
        } else if (this.value === 'Card') {
          cardDiv?.classList.remove('d-none');
        }
      });
    }
});

