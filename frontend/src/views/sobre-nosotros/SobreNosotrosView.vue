<template>
  <main class="about-view">
    <section class="about-hero">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <p class="eyebrow">SiempreGym</p>
        <h1>Entrenamiento simple, cercano y constante</h1>
        <p class="hero-text">
          Somos un gimnasio pensado para acompañarte con clases grupales,
          seguimiento profesional y una forma flexible de organizar tu rutina.
        </p>
      </div>
    </section>

    <section class="about-section intro-grid">
      <article class="mission-card">
        <p class="eyebrow">Nuestra misión</p>
        <h2>Bienestar, comunidad y movimiento accesible</h2>
        <p>
          En SiempreGym creemos que entrenar no debería sentirse complicado.
          Diseñamos espacios de trabajo claros, grupos cuidados y propuestas
          adaptadas para que cada persona pueda sostener su proceso.
        </p>
      </article>

      <div class="value-list" aria-label="Pilares de SiempreGym">
        <article v-for="item in missionPillars" :key="item.title" class="value-card">
          <span class="card-index">{{ item.number }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </article>
      </div>
    </section>

    <section class="about-section">
      <div class="section-heading">
        <p class="eyebrow">Actividades destacadas</p>
        <h2>Clases para distintos ritmos y objetivos</h2>
      </div>

      <div class="activity-grid">
        <article v-for="activity in highlightedActivities" :key="activity.name" class="activity-card">
          <h3>{{ activity.name }}</h3>
          <p>{{ activity.description }}</p>
        </article>
      </div>
    </section>

    <section class="about-section team-section">
      <div class="section-heading">
        <p class="eyebrow">Equipo</p>
        <h2>Profesionales que acompañan de verdad</h2>
      </div>

      <div class="team-grid">
        <article v-for="member in teamMembers" :key="member.name" class="team-card">
          <div class="avatar">{{ member.initials }}</div>
          <div>
            <h3>{{ member.name }}</h3>
            <p class="specialty">{{ member.specialty }}</p>
            <p>{{ member.description }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="about-section benefits-section">
      <div class="section-heading">
        <p class="eyebrow">Beneficios</p>
        <h2>Una experiencia pensada para entrenar sin vueltas</h2>
      </div>

      <div class="benefits-grid">
        <article v-for="benefit in benefits" :key="benefit" class="benefit-card">
          {{ benefit }}
        </article>
      </div>
    </section>
  </main>
</template>

<script setup>
const missionPillars = [
  {
    number: "01",
    title: "Bienestar integral",
    description: "Entrenamientos que combinan fuerza, movilidad y recuperación.",
  },
  {
    number: "02",
    title: "Comunidad",
    description: "Grupos reducidos, trato cercano y un ambiente donde es fácil volver.",
  },
  {
    number: "03",
    title: "Accesibilidad",
    description: "Reservas simples, horarios variados y clases para distintos niveles.",
  },
];

const highlightedActivities = [
  {
    name: "Yoga",
    description: "Prácticas enfocadas en movilidad, respiración y equilibrio corporal.",
  },
  {
    name: "Funcional",
    description: "Circuitos dinámicos para mejorar fuerza, coordinación y resistencia.",
  },
  {
    name: "Pilates",
    description: "Trabajo consciente de postura, control y estabilidad del core.",
  },
  {
    name: "Cross Training",
    description: "Sesiones intensas con ejercicios variados y seguimiento técnico.",
  },
];

const teamMembers = [
  {
    initials: "LC",
    name: "Laura Cáceres",
    specialty: "Entrenamiento funcional",
    description: "Planifica clases progresivas y acompaña a quienes retoman actividad física.",
  },
  {
    initials: "MN",
    name: "Mateo Núñez",
    specialty: "Fuerza y acondicionamiento",
    description: "Coordina sesiones de Cross Training con foco en técnica y seguridad.",
  },
  {
    initials: "VS",
    name: "Valentina Soto",
    specialty: "Yoga y Pilates",
    description: "Integra movilidad, respiración y control postural en cada encuentro.",
  },
];

const benefits = [
  "Clases grupales",
  "Horarios flexibles",
  "Seguimiento personalizado",
  "Reservas online",
];
</script>

<style scoped>
.about-view {
  background: #572c57;
  color: #f5f5f5;
  min-height: calc(100vh - 140px);
}

.about-hero {
  align-items: center;
  background-image: url("/hero-background.jpg");
  background-position: center;
  background-size: cover;
  display: flex;
  min-height: 420px;
  padding: 120px 24px 72px;
  position: relative;
}

.hero-overlay {
  background: rgba(87, 44, 87, 0.76);
  inset: 0;
  position: absolute;
}

.hero-content {
  margin: 0 auto;
  max-width: 1080px;
  position: relative;
  width: 100%;
  z-index: 1;
}

.eyebrow {
  color: #f6ea98;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
}

.hero-content h1 {
  max-width: 760px;
}

.hero-text {
  color: rgba(245, 245, 245, 0.84);
  font-size: 1.05rem;
  line-height: 1.7;
  max-width: 640px;
}

.about-section {
  margin: 0 auto;
  max-width: 1120px;
  padding: 56px 24px 0;
}

.intro-grid {
  display: grid;
  gap: 24px;
  grid-template-columns: 1.1fr 1fr;
}

.mission-card,
.value-card,
.activity-card,
.team-card,
.benefit-card {
  border: 1px solid #9f5f91;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.mission-card {
  background: #fff;
  color: #4a3a4a;
  padding: 32px;
}

.mission-card h2 {
  color: #572c57;
}

.mission-card .eyebrow{
  color: #9f5f91;
}

.mission-card p:not(.eyebrow),
.value-card p,
.activity-card p,
.team-card p {
  color: #4a3a4a;
  font-size: 0.98rem;
  letter-spacing: 0;
  line-height: 1.65;
}

.value-list {
  display: grid;
  gap: 16px;
}

.value-card,
.activity-card,
.team-card {
  background: #fff;
  color: #4a3a4a;
  padding: 24px;
}

.card-index {
  color: #9f5f91;
  display: block;
  font-family: "Anton", sans-serif;
  font-size: 1.45rem;
  margin-bottom: 8px;
}

.section-heading {
  margin-bottom: 24px;
  max-width: 760px;
}

.activity-grid,
.team-grid,
.benefits-grid {
  display: grid;
  gap: 18px;
}

.activity-grid {
  grid-template-columns: repeat(4, 1fr);
}

.activity-card {
  min-height: 190px;
}

.activity-card h3,
.team-card h3 {
  color: #572c57;
}

.team-section,
.benefits-section {
  padding-bottom: 0;
}

.team-grid {
  grid-template-columns: repeat(3, 1fr);
}

.team-card {
  display: flex;
  gap: 16px;
}

.avatar {
  align-items: center;
  background: linear-gradient(135deg, #9f5f91 0%, #572c57 100%);
  border-radius: 50%;
  color: #f6ea98;
  display: flex;
  flex: 0 0 56px;
  font-family: "Anton", sans-serif;
  font-size: 1.1rem;
  height: 56px;
  justify-content: center;
  letter-spacing: 0;
  width: 56px;
}

.specialty {
  color: #9f5f91 !important;
  font-weight: 700;
  margin-bottom: 10px;
}

.benefits-section {
  padding-bottom: 64px;
}

.benefits-grid {
  grid-template-columns: repeat(4, 1fr);
}

.benefit-card {
  background: #9f5f91;
  color: #f6ea98;
  font-family: "Poppins", sans-serif;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.35;
  padding: 18px;
  text-align: center;
}

@media (max-width: 1024px) {
  .activity-grid,
  .benefits-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .team-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .about-hero {
    min-height: 360px;
    padding: 108px 20px 52px;
  }

  .intro-grid {
    grid-template-columns: 1fr;
  }

  .about-section {
    padding: 40px 20px 0;
  }

  .mission-card,
  .value-card,
  .activity-card,
  .team-card {
    padding: 20px;
  }

  .team-card {
    align-items: flex-start;
  }
}

@media (max-width: 520px) {
  .about-hero {
    padding-left: 16px;
    padding-right: 16px;
  }

  .hero-text,
  .mission-card p:not(.eyebrow),
  .value-card p,
  .activity-card p,
  .team-card p {
    font-size: 0.9rem;
  }

  .activity-grid,
  .benefits-grid {
    grid-template-columns: 1fr;
  }

  .team-card {
    display: block;
  }

  .avatar {
    margin-bottom: 14px;
  }
}
</style>
