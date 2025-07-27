import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { applyHass } from 'custom-card-helpers'; // For hass object
@customElement('SmartHome-Copilot-card')
export class SmartHomeCopilotCard extends LitElement {
  static styles = css`
    :host {
      display: block;
    }
    ha-card {
      padding: 16px;
    }
    ul {
      list-style: none;
      padding: 0;
    }
    li {
      margin-bottom: 16px;
      border-bottom: 1px solid #eee;
      padding-bottom: 16px;
    }
    pre {
      background-color: #f0f0f0;
      padding: 10px;
      overflow-x: auto;
      border-radius: 4px;
      margin-top: 8px;
    }
    .details {
      display: none; /* Initially hidden */
    }
    .details[open] {
      display: block;
    }
    .error {
      color: red;
    }
  `;
  @property({ type: Object }) hass; // Home Assistant object
  @property({ type: Array }) suggestions = [];
  @state() loading = true;
  @state() error = null;

  static LOCALIZED_STRINGS = {
    en: {
      title: 'AI Automation Suggestions',
      loading: 'Loading suggestions...',
      details: 'Details',
      copyYaml: 'Copy YAML',
      accept: 'Accept',
      decline: 'Decline',
      copied: 'YAML code copied to clipboard!',
      fetchError: 'Failed to fetch suggestions.',
      errorPrefix: 'Error: '
    },
    de: {
      title: 'KI-Automatisierungsvorschläge',
      loading: 'Vorschläge werden geladen...',
      details: 'Details',
      copyYaml: 'YAML kopieren',
      accept: 'Annehmen',
      decline: 'Ablehnen',
      copied: 'YAML-Code in die Zwischenablage kopiert!',
      fetchError: 'Fehler beim Abrufen der Vorschläge.',
      errorPrefix: 'Fehler: '
    }
  };

  get strings() {
    const lang = (this.hass?.language || 'en').split('-')[0];
    return SmartHomeCopilotCard.LOCALIZED_STRINGS[lang] || SmartHomeCopilotCard.LOCALIZED_STRINGS.en;
  }
  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }
  async fetchData() {
    this.loading = true;
    this.error = null;
    try {
      const response = await this.hass.callApi('GET', '/api/SmartHome_Copilot/suggestions');
      this.suggestions = response;
    } catch (err) {
      this.error = err.message || this.strings.fetchError;
    } finally {
      this.loading = false;
    }
  }
  toggleDetails(suggestion) {
    suggestion.showDetails = !suggestion.showDetails;
    this.requestUpdate(); // Ensure re-render
  }
  copyYaml(yaml) {
    navigator.clipboard.writeText(yaml);
    this.dispatchEvent(new CustomEvent('hass-notification', {
      detail: {
        type: 'info',
        message: this.strings.copied,
      },
    }));
  }
  async handleSuggestionAction(suggestionId, action) {
    try {
      const response = await this.hass.callApi('POST', `/api/SmartHome_Copilot/${action}/${suggestionId}`);
      if (response.success) {
        this.fetchData(); // Refresh suggestions after action
      } else {
        this.error = response.error || `Failed to ${action} suggestion.`;
      }
    } catch (err) {
      this.error = err.message || `Failed to ${action} suggestion.`;
    }
  }
  render() {
    return html`
      <ha-card>
        <div>
          <h2>${this.strings.title}</h2>
          ${this.loading
            ? html`<p>${this.strings.loading}</p>`
            : this.error
              ? html`<p class="error">${this.strings.errorPrefix}${this.error}</p>`
              : html`
                  <ul>
                    ${this.suggestions.map(suggestion => html`
                      <li>
                        <h3>${suggestion.title}</h3>
                        <p>${suggestion.shortDescription}</p>
                        <button @click="${() => this.toggleDetails(suggestion)}">${this.strings.details}</button>
                        <div class="details" ?open="${suggestion.showDetails}">
                          <p>${suggestion.detailedDescription}</p>
                          <pre><code class="language-yaml">${suggestion.yamlCode}</code></pre>
                          <button @click="${() => this.copyYaml(suggestion.yamlCode)}">${this.strings.copyYaml}</button>
                          <button @click="${() => this.handleSuggestionAction(suggestion.id, 'accept')}">${this.strings.accept}</button>
                          <button @click="${() => this.handleSuggestionAction(suggestion.id, 'decline')}">${this.strings.decline}</button>
                        </div>
                      </li>
                    `)}
                  </ul>
                `}
        </div>
      </ha-card>
    `;
  }
  setConfig(config) {
    // Optional: Handle any configuration options passed to the card
  }
  set hass(hass) {
    applyHass(this, hass);
  }
  get hass() {
    return this._hass;
  }
}
// Provide a fallback registration if the module is loaded directly
if (customElements.get('SmartHome-Copilot-card') === undefined) {
  customElements.define('SmartHome-Copilot-card', SmartHomeCopilotCard);
}
