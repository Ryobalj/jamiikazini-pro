// src/utils/retryWithBackoff.js
export const retryWithExponentialBackoff = async (
  fn,
  maxRetries = 3,
  initialDelay = 1000
) => {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // If it's a rate limit error, wait longer
      if (error.response?.status === 429) {
        const delay = initialDelay * Math.pow(2, i); // Exponential backoff
        console.log(`⏳ Rate limited. Retrying in ${delay}ms... (attempt ${i + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        // For other errors, don't retry
        throw error;
      }
    }
  }
  
  throw lastError;
};