from django.shortcuts import render, get_object_or_404, HttpResponse, reverse, redirect
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

# import in the settings
from django.conf import settings

# import in stripe
import stripe

# import in the book
from books.models import Book

# import in the purchase
from .models import Purchase
from django.contrib.auth.models import User

# Create your views here.


def checkout(request):
    # tell Stripe what my api_key is
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # retrieve my shopping cart
    cart = request.session.get('shopping_cart', {})

    # create our line items
    line_items = []

    # go through each book in the shopping cart
    for book_id, book in cart.items():
        # retrieve the book by its id from the database
        book_model = get_object_or_404(Book, pk=book_id)

        # create line item
        # you see all the possible properties of a line item at:
        # https://stripe.com/docs/api/invoices/line_item
        item = {
            "name": book_model.title,
            "amount": int(book_model.cost * 100),
            "quantity": book['qty'],
            "currency": "usd",
            "description": book_model.id
        }

        line_items.append(item)

    # get the current website
    current_site = Site.objects.get_current()

    # get the domain name
    domain = current_site.domain

    # create a payment session to represent the current transaction
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],  # take credit cards
        line_items=line_items,
        client_reference_id=request.user.id,
        success_url=domain + reverse("checkout_success"),
        cancel_url=domain + reverse("checkout_cancelled")
    )

    return render(request, "checkout/checkout.template.html", {
        "session_id": session.id,
        "public_key": settings.STRIPE_PUBLISHABLE_KEY
    })


def checkout_success(request):
    request.session["shopping_cart"] = {}
    messages.success(request, "Your purchases been completed")
    return redirect(reverse('all_books_route'))
    # return HttpResponse("checkout success")


def checkout_cancelled(request):
    return HttpResponse("checkout cancelled")


@csrf_exempt
def payment_completed(request):
    # retrieve the information from the payment (also known as the payload)
    # this will contains the information sent out, like the line items
    payload = request.body

    # verify that the payment is legit
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    endpoint_secret = "whsec_zy5aR45jWes3CqkknYltzOhv77UiKWW0"
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret)
    except ValueError:
        # invalid payload
        # status 400 means forbidden (this means someone tried to s
        # poof a stripe payemnt)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # invalid signature
        return HttpResponse(status=400)

    # handle the payment proper
    if event["type"] == "checkout.session.completed":
        # retrieve the session data
        session = event['data']['object']

        # do whatever I want with the session
        handle_payment(session)

    # status 200 means everything's ok
    return HttpResponse(status=200)


def handle_payment(session):
    print(session)
    user = get_object_or_404(User, pk=session["client_reference_id"])

    for line_item in session["display_items"]:
        book_id = int(line_item["custom"]["description"])
        book_model = get_object_or_404(Book, pk=book_id)

        # create the purchase model
        purchase = Purchase()
        purchase.book_id = book_model
        purchase.user_id = user
        purchase.save()
