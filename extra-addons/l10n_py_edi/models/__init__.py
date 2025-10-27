# These must be firsts because python loading sequence
from . import edi_document_type
from . import edi_transaction_type
from . import account_tax_type
from . import edi_presence
from . import account_payment_term
# Then loads
from . import account_fiscal_position
from . import account_journal
from . import account_move
from . import account_tax
from . import account_tax_application_type
from . import account_tax_excise_category
from . import edi_issue_reason
from . import edi_issue_reason_picking
from . import edi_issue_responsible
from . import res_company
from . import res_config_settings
from . import uom_uom
from . import edi_certificate
from . import res_partner
from . import product_product
from . import stock_picking
from . import stock_picking_type
# from . import edi_batch
from . import l10n_latam_identification_type
from . import edi_reversion_document_type
from . import edi_document_cancel
from . import edi_document_invalid
from . import edi_document_nomination
from . import res_config_custom
from . import signxml
from . import edi_transport_type
from . import edi_transport_mode
from . import fleet_vehicle