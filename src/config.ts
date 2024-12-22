import dotenv from 'dotenv';
import Joi from 'joi';

dotenv.config();

// Define the schema for validation
const envVarsSchema = Joi.object({
  PORT: Joi.number().default(3000),
  ELAWAY_USER: Joi.string().email().required(),
  ELAWAY_CLIENT_ID: Joi.string().default('1'),
  ELAWAY_CLIENT_SECRET: Joi.string().required(),
  ELAWAY_PASSWORD: Joi.string().required(),
  POLLING_INTERVAL: Joi.number().default(60000),
  CLIENT_ID: Joi.string().required()
}).unknown();

// Validate environment variables
const { value: envVars, error } = envVarsSchema
  .prefs({ errors: { label: 'key' } })
  .validate(process.env);

if (error) {
  throw new Error(`Config validation error: ${error.message}`);
}

// Export the validated config
const config = {
  port: envVars.PORT,
  elawayUser: envVars.ELAWAY_USER,
  elawayPassword: envVars.ELAWAY_PASSWORD,
  elawayClientId: envVars.ELAWAY_CLIENT_ID,
  elawayClientSecret: envVars.ELAWAY_CLIENT_SECRET,
  pollingInterval: envVars.POLLING_INTERVAL,
  clientId: envVars.CLIENT_ID,
};

export default config;
