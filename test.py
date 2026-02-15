from templates import template_engine, OfferData
from config_schema import Language, ServiceConfig, ChannelConfig, ServiceType
import logging

logging.basicConfig(level=logging.INFO)

def test_rendering():
    offer = OfferData(
        service_type='CREDIT_CARD',
        provider='Test Bank',
        title_en='Great Offer',
        description_en='Details here',
        referral_link='http://test.com'
    )
    service_config = ServiceConfig(
        service_type=ServiceType.CREDIT_CARD,
        display_name_en='Credit Cards',
        icon='💳',
        channel=ChannelConfig(channel_id='@test_channel', language_mode='single')
    )
    
    res = template_engine.render(offer, service_config, 0)
    print('--- Rendered Message ---')
    print(res)
    print('-----------------------')
    assert 'Test Bank' in res
    assert 'Great Offer' in res

if __name__ == '__main__':
    try:
        test_rendering()
        print('✅ Tests passed!')
    except Exception as e:
        print(f'❌ Tests failed: {e}')
        import traceback
        traceback.print_exc()
