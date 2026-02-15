from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from enum import Enum
import yaml
import os

class ServiceType(str, Enum):
    CREDIT_CARD = "credit_card"
    LOAN_PERSONAL = "loan_personal"
    LOAN_BUSINESS = "loan_business"
    LOAN_HOME = "loan_home"
    BANK_ACCOUNT_SAVINGS = "bank_account_savings"
    BANK_ACCOUNT_CURRENT = "bank_account_current"
    CREDIT_BUILDER = "credit_builder"
    INSURANCE_HEALTH = "insurance_health"
    INSURANCE_VEHICLE = "insurance_vehicle"
    INSURANCE_PA = "insurance_pa"
    DEMAT_ACCOUNT = "demat_account"
    INVESTMENT_MUTUAL_FUND = "investment_mutual_fund"
    INVESTMENT_FIXED_INCOME = "investment_fixed_income"

class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    GUJARATI = "gu"

@dataclass
class ChannelConfig:
    channel_id: str
    language_mode: str
    enabled: bool = True
    rate_limit_per_hour: int = 10
    default_language: Language = Language.ENGLISH

    def __post_init__(self):
        if not self.channel_id.startswith("@"):
            raise ValueError(f"Channel ID must start with @: {self.channel_id}")

@dataclass
class ServiceConfig:
    service_type: ServiceType
    channel: ChannelConfig
    display_name_en: str
    display_name_hi: Optional[str] = None
    display_name_gu: Optional[str] = None
    icon: str = "📌"
    requires_kyc: bool = True
    enabled: bool = True

class ConfigManager:
    def __init__(self, config_path: str = "services_config.yaml"):
        self.config_path = config_path
        self.services: Dict[ServiceType, ServiceConfig] = {}
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            self._create_default_config()
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        for service_key, service_data in data['services'].items():
            service_type = ServiceType(service_key)
            channel = ChannelConfig(
                channel_id=service_data['channel_id'],
                language_mode=service_data.get('language_mode', 'single'),
                enabled=service_data.get('enabled', True),
                rate_limit_per_hour=service_data.get('rate_limit_per_hour', 10),
                default_language=Language(service_data.get('default_language', 'en')))
            service_config = ServiceConfig(
                service_type=service_type,
                channel=channel,
                display_name_en=service_data['display_name']['en'],
                display_name_hi=service_data['display_name'].get('hi'),
                display_name_gu=service_data['display_name'].get('gu'),
                icon=service_data.get('icon', '📌'),
                requires_kyc=service_data.get('requires_kyc', True),
                enabled=service_data.get('enabled', True))
            self.services[service_type] = service_config

    def _create_default_config(self):
        default_config = {
            'services': {
                'credit_card': {'channel_id': '@Fin_CC_Offers', 'language_mode': 'multi', 'display_name': {'en': 'Credit Cards', 'hi': 'क्रेडिट कार्ड', 'gu': 'ક્રેડિટ કાર્ડ'}, 'icon': '💳', 'requires_kyc': True, 'enabled': True, 'rate_limit_per_hour': 10},
                'loan_personal': {'channel_id': '@Fin_Personal_Loans', 'language_mode': 'multi', 'display_name': {'en': 'Personal Loans', 'hi': 'व्यक्तिगत ऋण', 'gu': 'વ્યક્તિગત લોન'}, 'icon': '💰', 'requires_kyc': True},
                'loan_business': {'channel_id': '@Fin_Business_Loans', 'language_mode': 'single', 'display_name': {'en': 'Business Loans', 'hi': 'व्यवसाय ऋण', 'gu': 'બિઝનેસ લોન'}, 'icon': '🏢'},
                'loan_home': {'channel_id': '@Fin_Home_Loans', 'language_mode': 'multi', 'display_name': {'en': 'Home Loans', 'hi': 'गृह ऋण', 'gu': 'હોમ લોન'}, 'icon': '🏠'},
                'bank_account_savings': {'channel_id': '@Fin_Savings_Accounts', 'language_mode': 'multi', 'display_name': {'en': 'Savings Accounts', 'hi': 'बचत खाते', 'gu': 'બચત ખાતા'}, 'icon': '🏦'},
                'bank_account_current': {'channel_id': '@Fin_Current_Accounts', 'language_mode': 'single', 'display_name': {'en': 'Current Accounts', 'hi': 'चालू खाते', 'gu': 'ચાલુ ખાતા'}, 'icon': '🏦'},
                'credit_builder': {'channel_id': '@Fin_Credit_Builder', 'language_mode': 'multi', 'display_name': {'en': 'Credit Builder', 'hi': 'क्रेडिट निर्माता', 'gu': 'ક્રેડિટ બિલ્ડર'}, 'icon': '📈'},
                'insurance_health': {'channel_id': '@Fin_Health_Insurance', 'language_mode': 'multi', 'display_name': {'en': 'Health Insurance', 'hi': 'स्वास्थ्य बीमा', 'gu': 'આરોગ્ય વીમો'}, 'icon': '🏥'},
                'insurance_vehicle': {'channel_id': '@Fin_Vehicle_Insurance', 'language_mode': 'multi', 'display_name': {'en': 'Vehicle Insurance', 'hi': 'वाहन बीमा', 'gu': 'વાહન વીમો'}, 'icon': '🚗'},
                'insurance_pa': {'channel_id': '@Fin_PA_Insurance', 'language_mode': 'single', 'display_name': {'en': 'Personal Accident Insurance', 'hi': 'व्यक्तिगत दुर्घटना बीमा', 'gu': 'વ્યક્તિગત અકસ્માત વીમો'}, 'icon': '🛡️'},
                'demat_account': {'channel_id': '@Fin_Demat', 'language_mode': 'multi', 'display_name': {'en': 'Demat Accounts', 'hi': 'डीमैट खाते', 'gu': 'ડિમેટ ખાતા'}, 'icon': '📊'},
                'investment_mutual_fund': {'channel_id': '@Fin_Mutual_Funds', 'language_mode': 'multi', 'display_name': {'en': 'Mutual Funds', 'hi': 'म्यूचुअल फंड', 'gu': 'મ્યુચ્યુઅલ ફંડ'}, 'icon': '💹'},
                'investment_fixed_income': {'channel_id': '@Fin_Fixed_Income', 'language_mode': 'single', 'display_name': {'en': 'Fixed Income', 'hi': 'निश्चित आय', 'gu': 'નિશ્ચિત આવક'}, 'icon': '📈'}
            }
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, sort_keys=False)

    def get_channel_for_service(self, service_type: ServiceType) -> str:
        if service_type not in self.services:
            raise ValueError(f"Unknown service type: {service_type}")
        service_config = self.services[service_type]
        if not service_config.enabled or not service_config.channel.enabled:
            raise ValueError(f"Service {service_type} is disabled")
        return service_config.channel.channel_id

    def update_channel_id(self, service_type: ServiceType, channel_id: str):
        if service_type not in self.services:
            raise ValueError(f"Unknown service type: {service_type}")
        if not channel_id.startswith("@"):
             raise ValueError("Channel ID must start with @")
        self.services[service_type].channel.channel_id = channel_id
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if 'services' not in data:
            data['services'] = {}
        service_key = service_type.value
        if service_key not in data['services']:
             data['services'][service_key] = {}
        data['services'][service_key]['channel_id'] = channel_id
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    def get_service_config(self, service_type: ServiceType) -> ServiceConfig:
        if service_type not in self.services:
            raise ValueError(f"Unknown service type: {service_type}")
        return self.services[service_type]

    def list_enabled_services(self) -> List[ServiceType]:
        return [stype for stype, config in self.services.items() if config.enabled and config.channel.enabled]

    def validate_service_type(self, service_type: str) -> ServiceType:
        try:
            return ServiceType(service_type)
        except ValueError:
            valid = [s.value for s in ServiceType]
            raise ValueError(f"Invalid service type: {service_type}. Valid: {valid}")

config_manager = ConfigManager()
