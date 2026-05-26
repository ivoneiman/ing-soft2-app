export const CLASS_STATUS = {
  ACTIVE: 'Activa',
  CANCELLED: 'Cancelada',
};

export const ENROLLMENT_STATUS = {
  PENDING_PAYMENT: 'pending_payment',
  PAID: 'paid',
  EXPIRED: 'expired',
  CANCELLED: 'cancelled',
};

export const PAYMENT_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
};

export const PAYMENT_METHOD = {
  MERCADO_PAGO: 'mercado_pago',
  CREDIT: 'credit',
};

export const CREDIT_STATUS = {
  AVAILABLE: 'available',
  USED: 'used',
  EXPIRED: 'expired',
};

export const STATUS_LABELS = {
  class: {
    [CLASS_STATUS.ACTIVE]: 'Activa',
    [CLASS_STATUS.CANCELLED]: 'Cancelada',
  },
  enrollment: {
    [ENROLLMENT_STATUS.PENDING_PAYMENT]: 'Pendiente de pago',
    [ENROLLMENT_STATUS.PAID]: 'Pagada',
    [ENROLLMENT_STATUS.EXPIRED]: 'Vencida',
    [ENROLLMENT_STATUS.CANCELLED]: 'Cancelada',
  },
  payment: {
    [PAYMENT_STATUS.APPROVED]: 'Aprobado',
    [PAYMENT_STATUS.REJECTED]: 'Rechazado',
    [PAYMENT_STATUS.PENDING]: 'Pendiente',
    [PAYMENT_STATUS.EXPIRED]: 'Vencido',
  },
  paymentMethod: {
    [PAYMENT_METHOD.MERCADO_PAGO]: 'Mercado Pago',
    [PAYMENT_METHOD.CREDIT]: 'Crédito',
  },
  credit: {
    [CREDIT_STATUS.AVAILABLE]: 'Disponible',
    [CREDIT_STATUS.USED]: 'Usado',
    [CREDIT_STATUS.EXPIRED]: 'Vencido',
  },
};

export function statusLabel(group, status) {
  return STATUS_LABELS[group]?.[status] || status || '-';
}
