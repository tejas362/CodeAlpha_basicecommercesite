from django.http import JsonResponse
import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, OrderItem, Order
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm, OrderCreateForm
from django.contrib.auth.decorators import login_required




def product_list(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'store/product_list.html', context)

def view_cart(request):
    # This is a placeholder. Cart functionality will be built later.
    return HttpResponse("<h1>Shopping Cart Page (Under Construction)</h1>")

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    context = {'product': product}
    return render(request, 'store/product_detail.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in directly
            messages.success(request, "Registration successful!")
            return redirect('product_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def update_cart_item(request):
    data = json.loads(request.body)
    productId_str = str(data.get('productId')) # Ensure it's a string key
    action = data.get('action')

    cart = request.session.get('cart', {}) # Get cart from session, or empty dict

    try:
        product = Product.objects.get(id=int(productId_str))
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    item_removed_flag = False

    if action == 'add':
        if productId_str not in cart:
            if product.stock > 0:
                cart[productId_str] = {'quantity': 1, 'price': str(product.price), 'name': product.name, 'image': product.imageURL}
            else:
                return JsonResponse({'message': 'Product out of stock', 'total_items': sum(item.get('quantity', 0) for item in cart.values())}, status=400)
        else:
            if cart[productId_str]['quantity'] < product.stock:
                cart[productId_str]['quantity'] += 1
            else:
                return JsonResponse({'message': 'Cannot add more, stock limit reached', 'total_items': sum(item.get('quantity', 0) for item in cart.values())}, status=400)

    elif action == 'remove':
        if productId_str in cart:
            cart[productId_str]['quantity'] -= 1
            if cart[productId_str]['quantity'] <= 0:
                del cart[productId_str]
                item_removed_flag = True
    elif action == 'delete': # For completely removing an item from cart page
        if productId_str in cart:
            del cart[productId_str]
            item_removed_flag = True

    request.session['cart'] = cart # Save cart back to session
    request.session.modified = True # Mark session as modified

    total_items = sum(item.get('quantity', 0) for item in cart.values())
    return JsonResponse({
        'message': 'Cart updated',
        'total_items': total_items,
        'cart': cart, # Send back the updated cart for potential dynamic updates
        'item_removed': item_removed_flag
    })

def get_cart_data(request):
    cart = request.session.get('cart', {})
    total_items = sum(item.get('quantity', 0) for item in cart.values())
    # Calculate total price for display if needed elsewhere
    total_price = sum(float(item.get('price', 0)) * item.get('quantity', 0) for item in cart.values())
    return JsonResponse({'total_items': total_items, 'cart': cart, 'total_price': total_price})

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items_list = []
    total_cart_price = 0

    for product_id_str, item_data in cart.items():
        try:
            # It's good to re-fetch product to ensure data consistency,
            # but for simplicity and performance with session, we use stored data.
            # Be mindful of price changes if you don't re-fetch.
            # product = Product.objects.get(id=int(product_id_str))
            # current_price = product.price
            current_price = float(item_data.get('price', 0)) # Using stored price
        except Product.DoesNotExist:
            # Product might have been deleted, handle gracefully (e.g., remove from cart)
            # For now, we assume product exists or rely on session data
            continue


        item_total_price = item_data.get('quantity', 0) * current_price
        cart_items_list.append({
            'id': product_id_str,
            'name': item_data.get('name', 'N/A'),
            'quantity': item_data.get('quantity', 0),
            'price': current_price, # Use current or stored price
            'image': item_data.get('image', ''),
            'total_price': item_total_price
        })
        total_cart_price += item_total_price

    context = {
        'cart_items': cart_items_list,
        'total_cart_price': total_cart_price,
        'is_empty': not bool(cart_items_list)
    }
    return render(request, 'store/view_cart.html', context)

def checkout(request):
    # This is a placeholder. Checkout functionality will be built in Phase 5.
    return HttpResponse("<h1>Checkout Page (Under Construction)</h1>")

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')

    cart_items_for_context = []
    current_total_cart_price = 0
    for product_id_str, item_data in cart.items():
        try:
            product = Product.objects.get(id=int(product_id_str)) # Fetch product for current info
            item_price = product.price # Use current price from DB
        except Product.DoesNotExist:
            messages.error(request, f"Product with ID {product_id_str} no longer exists and has been removed from your cart.")
            # Optionally remove from cart here
            del cart[product_id_str]
            request.session.modified = True
            continue

        quantity = item_data.get('quantity', 0)
        if quantity > product.stock:
            messages.error(request, f"Not enough stock for {product.name}. Available: {product.stock}. Requested: {quantity}. Please update your cart.")
            return redirect('view_cart')

        cart_items_for_context.append({
            'product': product,
            'quantity': quantity,
            'total_price': item_price * quantity
        })
        current_total_cart_price += item_price * quantity


    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total_paid = current_total_cart_price # Set the calculated total
            order.save() # Save order to get an ID

            for item_in_cart in cart_items_for_context:
                product_obj = item_in_cart['product']
                OrderItem.objects.create(
                    order=order,
                    product=product_obj,
                    price_at_purchase=product_obj.price, # Price at the moment of purchase
                    quantity=item_in_cart['quantity']
                )
                # Update stock
                product_obj.stock -= item_in_cart['quantity']
                product_obj.save()

            # Simulate payment for this task
            order.paid = True
            order.save()

            # Clear the cart from session
            del request.session['cart']
            request.session.modified = True

            messages.success(request, "Your order has been placed successfully!")
            # You might want to pass order_id to the created page
            return render(request, 'store/order_created.html', {'order': order})
        else: # Form is not valid
            for field, errors_list in form.errors.items():
                for error in errors_list:
                    messages.error(request, f"Error in {field}: {error}")
    else: # GET request
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items_for_context,
        'total_cart_price': current_total_cart_price,
        'form': form
    })

@login_required # Ensures only logged-in users can access this page
def order_history(request):
    # Fetch orders for the currently logged-in user, ordered by most recent
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
        'page_title': 'My Order History' # Optional: for the template title
    }
    return render(request, 'store/order_history.html', context)