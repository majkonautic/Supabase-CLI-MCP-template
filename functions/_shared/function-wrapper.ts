import { log } from "./logger.ts"

export function withLogging(functionName: string, handler: (req: Request) => Promise<Response>) {
  return async (req: Request): Promise<Response> => {
    await log(functionName, 'INFO', 'Function invoked', {
      method: req.method,
      url: req.url,
      headers: Object.fromEntries(req.headers.entries())
    })
    
    const startTime = Date.now()
    
    try {
      const response = await handler(req)
      const duration = Date.now() - startTime
      
      await log(functionName, 'INFO', 'Function completed', {
        status: response.status,
        duration: `${duration}ms`
      })
      
      return response
    } catch (error) {
      const duration = Date.now() - startTime
      
      await log(functionName, 'ERROR', 'Function failed', {
        error: error.message,
        stack: error.stack,
        duration: `${duration}ms`
      })
      
      throw error
    }
  }
}
