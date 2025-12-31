import { env } from '$env/dynamic/public';

/**
 * Vieši konfigūracijos kintamieji, naudojami frontend'e.
 */
export const appConfig = {
	apiBaseUrl: env.PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api',
	mediaBaseUrl: env.PUBLIC_MEDIA_BASE_URL ?? 'http://localhost:8000/media'
};
