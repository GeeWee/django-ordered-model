from django.db.models.signals import post_delete
from django.dispatch import receiver
from ordered_model.models import OrderedModelBase
from django.db.models import F


@receiver(post_delete, dispatch_uid="on_ordered_model_delete")
def on_ordered_model_delete(sender, instance, **kwargs):
    """
    This signal makes sure that when an OrderedModelBase is deleted via cascade database deletes.
    """

    """
    We're only interested in subclasses of OrderedModelBase.
    We want to be able to support 'extra_kwargs' on the delete()
    method, which we can't do if we do all our work in the signal. We add a property to signal whether or not
    the model's .delete() method was called, because if so - we don't need to do any more work.
    """
    if not issubclass(sender, OrderedModelBase) or getattr(instance, '_was_deleted_via_delete_method', None):
        return

    qs = instance.get_ordering_queryset()
    update_kwargs = {instance.order_field_name: F(instance.order_field_name) - 1}
    # Here we don't use a subQuery to get the value of the model, as it's already been deleted at this point
    # in the process, so we're actually unable to. We'll just have to pray that no other object has taken its
    # place from here until it got deleted.
    qs.filter(
        **{instance.order_field_name + "__gt": getattr(instance, instance.order_field_name)}
    ).update(**update_kwargs)
