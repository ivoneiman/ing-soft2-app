export const PAYMENT_TAB = {
  HISTORY: 'history',
  CREDITS: 'credits',
  ADMIN: 'admin',
};

export const PAYMENT_TABS = Object.values(PAYMENT_TAB);

export const PAYMENT_RETURN_STATUS = {
  SUCCESS: 'success',
  CREDIT: 'credit',
  PENDING: 'pending',
  FAILURE: 'failure',
};

export const PAYMENT_RETURN_MESSAGES = {
  [PAYMENT_RETURN_STATUS.SUCCESS]: { type: 'success', text: 'Pago aprobado' },
  [PAYMENT_RETURN_STATUS.CREDIT]: { type: 'success', text: 'Inscripción realizada utilizando crédito' },
  [PAYMENT_RETURN_STATUS.PENDING]: { type: 'pending', text: 'Pago pendiente' },
};
