from dataclasses import dataclass
from typing import Optional, Dict
from config_schema import Language, ServiceConfig, ChannelConfig
from datetime import datetime


@dataclass
class OfferData:
    service_type: str
    provider: str
    title_en: str
    title_hi: Optional[str] = None
    title_gu: Optional[str] = None
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    description_gu: Optional[str] = None
    referral_link: str = ""
    validity: Optional[str] = None
    terms: Optional[str] = None
    icon: str = "📌"


class TemplateEngine:

    DISCLAIMER_EN = "⚠️ This is a referral link. No financial advice. Verify all terms independently. No PII stored."
    DISCLAIMER_HI = "⚠️ यह एक रेफरल लिंक है। कोई वित्तीय सलाह नहीं। सभी शर्तों को स्वतंत्र रूप से सत्यापित करें।"
    DISCLAIMER_GU = "⚠️ આ રેફરલ લિંક છે. કોઈ નાણાકીય સલાહ નથી. બધી શરતો સ્વતંત્ર રીતે ચકાસો."

    FOOTER_EN = "📢 FinReferrals — Community-sourced financial offers"
    FOOTER_HI = "📢 FinReferrals — समुदाय-आधारित वित्तीय ऑफ़र"
    FOOTER_GU = "📢 FinReferrals — સમુદાય-આધારિત નાણાકીય ઑફર"

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[Language, str]:
        return {
            Language.ENGLISH: """{icon} **{service_name}**

🏦 **Provider:** {provider}
🎯 **Offer:** {title}
{description}
🔗 **Apply:** {link}
{validity}
{terms}

{disclaimer}

{footer}""",
            Language.HINDI: """{icon} **{service_name}**

🏦 **प्रदाता:** {provider}
🎯 **ऑफ़र:** {title}
{description}
🔗 **आवेदन करें:** {link}
{validity}
{terms}

{disclaimer}

{footer}""",
            Language.GUJARATI: """{icon} **{service_name}**

🏦 **પ્રદાતા:** {provider}
🎯 **ઓફર:** {title}
{description}
🔗 **અરજી કરો:** {link}
{validity}
{terms}

{disclaimer}

{footer}"""
        }

    def _get_field_with_fallback(self, offer: OfferData, field_prefix: str,
                                 language: Language) -> str:
        field_name = f"{field_prefix}_{language.value}"
        value = getattr(offer, field_name, None)

        if value:
            return value

        fallback_field = f"{field_prefix}_en"
        return getattr(offer, fallback_field, "")

    def render_single_language(self,
                               offer: OfferData,
                               service_config: ServiceConfig,
                               language: Language = Language.ENGLISH) -> str:
        template = self.templates[language]

        service_name = getattr(
            service_config, f"display_name_{language.value}",
            service_config.display_name_en) or service_config.display_name_en

        title = self._get_field_with_fallback(offer, "title", language)
        description = self._get_field_with_fallback(offer, "description",
                                                    language)

        disclaimer = getattr(self, f"DISCLAIMER_{language.value.upper()}",
                             self.DISCLAIMER_EN)
        footer = getattr(self, f"FOOTER_{language.value.upper()}",
                         self.FOOTER_EN)

        description_text = f"📝 {description}" if description else ""
        validity_text = f"⏰ **Valid until:** {offer.validity}" if offer.validity else ""
        terms_text = f"📋 **Terms:** {offer.terms}" if offer.terms else ""

        return template.format(icon=service_config.icon,
                               service_name=service_name,
                               provider=offer.provider,
                               title=title,
                               description=description_text,
                               link=offer.referral_link,
                               validity=validity_text,
                               terms=terms_text,
                               disclaimer=disclaimer,
                               footer=footer).strip()

    def render_multi_language(self,
                              offer: OfferData,
                              service_config: ServiceConfig,
                              languages: list[Language] = None) -> str:
        if languages is None:
            languages = [Language.ENGLISH, Language.HINDI, Language.GUJARATI]

        sections = []

        for lang in languages:
            title_field = f"title_{lang.value}"
            if not getattr(offer, title_field,
                           None) and lang != Language.ENGLISH:
                continue  # Skip language if no content

            sections.append(
                self.render_single_language(offer, service_config, lang))
            sections.append("─" * 40)  # Separator

        if sections and sections[-1].startswith("─"):
            sections.pop()

        return "\n\n".join(sections)

    def render_rotating_language(self,
                                 offer: OfferData,
                                 service_config: ServiceConfig,
                                 rotation_index: int = 0) -> str:
        languages = [Language.ENGLISH, Language.HINDI, Language.GUJARATI]
        selected_language = languages[rotation_index % len(languages)]
        return self.render_single_language(offer, service_config,
                                           selected_language)

    def render(self,
               offer: OfferData,
               service_config: ServiceConfig,
               rotation_index: int = 0) -> str:
        """
        Main render method - routes based on channel language_mode

        Args:
            offer: Offer data
            service_config: Service configuration
            rotation_index: Used for rotating mode

        Returns:
            Formatted Telegram message
        """
        mode = service_config.channel.language_mode

        if mode == "single":
            return self.render_single_language(
                offer, service_config, service_config.channel.default_language)
        elif mode == "multi":
            return self.render_multi_language(offer, service_config)
        elif mode == "rotating":
            return self.render_rotating_language(offer, service_config,
                                                 rotation_index)
        else:
            return self.render_single_language(offer, service_config,
                                               Language.ENGLISH)


template_engine = TemplateEngine()


def test_templates():
    from config_schema import ServiceType, config_manager

    test_offer = OfferData(service_type="credit_card",
                           provider="HDFC Bank",
                           title_en="5% cashback on all transactions",
                           title_hi="सभी लेनदेन पर 5% कैशबैक",
                           title_gu="બધા વ્યવહારો પર 5% કેશબેક",
                           description_en="Unlimited cashback, no caps",
                           description_hi="असीमित कैशबैक, कोई सीमा नहीं",
                           description_gu="અમર્યાદિત કેશબેક, કોઈ મર્યાદા નથી",
                           referral_link="https://hdfc.com/ref/abc123",
                           validity="31 Dec 2026",
                           icon="💳")

    service_config = config_manager.get_service_config(ServiceType.CREDIT_CARD)

    print("=== SINGLE LANGUAGE (English) ===")
    print(template_engine.render_single_language(test_offer, service_config))
    print("\n" + "=" * 60 + "\n")

    print("=== MULTI LANGUAGE ===")
    print(template_engine.render_multi_language(test_offer, service_config))
    print("\n" + "=" * 60 + "\n")

    print("=== ROTATING LANGUAGE (Hindi) ===")
    print(
        template_engine.render_rotating_language(test_offer, service_config,
                                                 1))


if __name__ == "__main__":
    test_templates()
