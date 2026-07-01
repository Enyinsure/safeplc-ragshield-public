# Visual Evidence Examples

| # | Evidence ID | visual_type | Industrial meaning | Hit keywords | M-EPI handling | Audit chain | Why text-only is not enough |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `pdf_page_01965` | `wiring_error_diagram` | Wrong wiring diagram or hazardous wiring note. | wiring error, warning, short-circuit | `keep_as_risk_evidence` | Yes | The visual layout explains which terminal or wire path is risky. |
| 2 | `pdf_page_00203` | `terminal_layout` | Terminal wiring rule table. | terminal, wiring, L+, M, DI, DQ | `keep` | Yes | The table/terminal positions are spatial and easy to lose in plain text. |
| 3 | `pdf_page_cpu_module` | `module_front_panel` | CPU module interface and front panel reference. | CPU, PN/DP, X1, X2 | `keep` | Yes | Visual port positions disambiguate interface references. |
| 4 | `pdf_page_led_panel` | `module_front_panel` | LED/RUN/STOP/ERROR status page. | RUN, STOP, ERROR, LED | `keep` unless paired with real fault semantics | Yes | Indicator names alone are not a risk; placement and state legends matter. |
| 5 | `pdf_page_diagnostic_alarm` | `diagnostic_alarm_page` | Diagnostic alarm explanation. | diagnostic, alarm, fault | `keep_as_risk_evidence` | Yes | Alarm tables must be preserved for safety reasoning. |
| 6 | `pdf_page_network_topology` | `network_topology` | PROFINET or distributed I/O topology. | topology, network, PN | `keep` | Yes | Topology edges and device relationships are visual. |
| 7 | `pdf_page_power_install` | `power_supply_installation` | Installation and power supply constraints. | power, supply, grounding | `keep_as_risk_evidence` if warning terms appear | Yes | Cable routing and grounding diagrams carry safety meaning. |
| 8 | `pdf_page_parameter_table` | `parameter_table` | Parameter ranges and ratings. | rated voltage, current, range | `keep` | Yes | Numeric rows need table provenance and page traceability. |
| 9 | `pdf_page_safety_warning` | `safety_warning_page` | Safety warning statement. | warning, danger, qualified personnel | `keep_as_risk_evidence` | Yes | Safety warnings should be retained, not filtered as dangerous words. |
| 10 | `pdf_page_order_number` | `model_order_number_page` | Model/order number mapping. | 6ES, order number, model | `keep` | Yes | Clarification depends on exact model/order identifiers. |

