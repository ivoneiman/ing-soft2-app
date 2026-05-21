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
};

export const PAYMENT_METHOD = {
  MERCADO_PAGO: 'mercado_pago',
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
  },
  paymentMethod: {
    [PAYMENT_METHOD.MERCADO_PAGO]: 'Mercado Pago',
  },
};

export function statusLabel(group, status) {
  return STATUS_LABELS[group]?.[status] || status || '-';
}

