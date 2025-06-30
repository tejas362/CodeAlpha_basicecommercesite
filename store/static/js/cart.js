// Ensure this script is loaded after the DOM is ready, or use defer in script tag
document.addEventListener('DOMContentLoaded', function() {
    updateCartIcon(); // Initial cart count update

    const cartButtons = document.querySelectorAll('.add-to-cart-btn, .update-cart-btn, .delete-cart-item-btn');

    cartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.product;
            const action = this.dataset.action;
            console.log('productId:', productId, 'action:', action);
            updateUserCart(productId, action);
        });
    });
});

function updateUserCart(productId, action) {
    const url = '/update_item/'; // This URL needs to be defined in Django

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'), // Function to get CSRF token
        },
        body: JSON.stringify({'productId': productId, 'action': action})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log('Cart updated:', data);
        document.getElementById('cart-total').innerText = data.total_items;
        if (data.message) {
            // alert(data.message); // Simple feedback
        }
        // If on cart page and item quantity becomes 0, or item is deleted, reload
        if (window.location.pathname === '/cart/' && (data.item_removed || (data.cart && data.cart[productId] && data.cart[productId].quantity <= 0))) {
            window.location.reload();
        } else if (window.location.pathname === '/cart/' && (action === 'add' || action === 'remove')) {
            // For +/- buttons on cart page, update quantities and totals dynamically if desired
            // Or simply reload like above for now. For a better UX, update specific elements.
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error updating cart:', error);
        // alert('Error updating cart. Please try again.');
    });
}

function updateCartIcon() {
    fetch('/get_cart_data/') // Django URL to get current cart info
        .then(response => response.json())
        .then(data => {
            if (data.total_items !== undefined) {
                document.getElementById('cart-total').innerText = data.total_items;
            }
        })
        .catch(e => console.error("Error fetching initial cart count:", e));
}

// Function to get CSRF token (Django specific)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}