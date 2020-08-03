from django.shortcuts import render, get_object_or_404, redirect, reverse, HttpResponse
from django.contrib import messages

from books.models import Book


# Create your views here.
def add_to_cart(request, book_id):

    # the cart object is a dictionary
    cart = request.session.get('shopping_cart', {})

    # check if the book_id I want to add already exists inside the cart already
    # if the book is not in the shopping cart
    if book_id not in cart:
        book = get_object_or_404(Book, pk=book_id)

        # add the book to cart
        cart[book_id] = {
            'id': book_id,
            'title': book.title,
            'cost': float(book.cost),
            'qty': 1,
            'total_cost': float(book.cost)
        }

        messages.success(
            request, f"Added book '{book.title}' to the shopping cart")

    else:
        # if the book already exists in the cart
        cart[book_id]['qty'] += 1

    # save the shopping cart back to session
    request.session['shopping_cart'] = cart
    return redirect(reverse('view_cart'))


def view_cart(request):
    # loading the content of the 'shopping_cart' from the session
    cart = request.session.get('shopping_cart', {})

    total = 0
    for k, v in cart.items():
        # have to convert back to float because
        # session can only store strings
        total += float(v['cost']) * int(v['qty'])

    return render(request, 'cart/view_cart.template.html', {
        "cart": cart,
        "total": total
    })


def remove_from_cart(request, book_id):
    cart = request.session["shopping_cart"]
    if book_id in cart:
        # removew from the cart
        del cart[book_id]

        # save back the shopping cart into the session
        request.session['shopping_cart'] = cart

        messages.success(request, "The item has been removed")

    return redirect(reverse('view_cart'))


def update_quantity(request, book_id):
    # get the shopping cart
    cart = request.session["shopping_cart"]
    if book_id in cart:
        # update the quantity
        cart[book_id]['qty'] = request.POST['qty']
        cart[book_id]['total_cost'] = int(request.POST['qty']) * float(cart[book_id]['cost'])

        # save the cart back into the session
        request.session["shopping_cart"] = cart
        messages.success(request, f"Quantity for {cart[book_id]['title']} has been changed")

        return redirect(reverse('view_cart'))
    else:
        messages.success(request, "The book doesn't exist in your cart.")
        return redirect(reverse('view_cart'))