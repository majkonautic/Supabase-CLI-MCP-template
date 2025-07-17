const LOG_COLLECTOR_URL = 'https://unozoiqfcmysghevuqkb.supabase.co/functions/v1/log-collector'

export async function log(
  functionName: string, 
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG',
  message: string,
  metadata?: any
) {
  // Always log to console (for local dev)
  console.log(`[${level}] ${message}`, metadata || '')
  
  // Send to webhook in production
  if (Deno.env.get('DENO_DEPLOYMENT_ID')) {
    try {
      await fetch(LOG_COLLECTOR_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`
        },
        body: JSON.stringify({
          function_name: functionName,
          level,
          message,
          metadata
        })
      })
    } catch (err) {
      console.error('Failed to send log to webhook:', err)
    }
  }
}
