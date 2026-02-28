(function bootstrapApiClient(global) {
    function resolveApiBaseUrl() {
        const validProtocol = window.location.protocol === 'http:' || window.location.protocol === 'https:';
        return validProtocol ? window.location.origin : 'http://127.0.0.1:8000';
    }

    async function parseApiPayload(response) {
        const text = await response.text();
        if (!text) {
            return {};
        }
        try {
            return JSON.parse(text);
        } catch {
            return {};
        }
    }

    function createLojaApiClient(options = {}) {
        const {
            getToken = () => null,
            onUnauthorized = () => {},
            onStatusChange = () => {}
        } = options;

        const baseUrl = resolveApiBaseUrl();

        async function request({ endpoint, method = 'GET', body = null, auth = true }) {
            const headers = {};
            if (body !== null) {
                headers['Content-Type'] = 'application/json';
            }

            const token = getToken();
            if (auth && token) {
                headers.Authorization = `Bearer ${token}`;
            }

            let response;
            try {
                response = await fetch(`${baseUrl}${endpoint}`, {
                    method,
                    headers,
                    body: body !== null ? JSON.stringify(body) : null
                });
            } catch {
                onStatusChange(false);
                throw new Error('Falha de conexao com o servidor.');
            }

            const payload = await parseApiPayload(response);
            if (!response.ok) {
                const message = payload?.detail || `Erro ${response.status}.`;
                const error = new Error(message);
                error.status = response.status;
                error.payload = payload;
                if (response.status === 401 && auth) {
                    onUnauthorized(error);
                }
                throw error;
            }

            onStatusChange(true);
            return payload;
        }

        return {
            baseUrl,
            request
        };
    }

    global.createLojaApiClient = createLojaApiClient;
})(window);
