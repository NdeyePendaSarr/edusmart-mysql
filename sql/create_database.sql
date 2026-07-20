-- =============================================================
-- Projet : EduSmart Decision Platform
-- Groupe : 2
-- Source : MySQL - Plateforme pédagogique (edusmart_learning)
-- Auteure : Ndeye Penda SARR
-- Fichier : create_database.sql
-- Description :
--   Script de creation de la base de donnees `edusmart_learning`
--   et de ses 6 tables (modules, cours, quiz, notes,
--   progression, temps_connexion).
--
-- Choix techniques :
--   - Moteur : InnoDB (support FK + transactions)
--   - Encodage : utf8mb4 + collation utf8mb4_unicode_ci
--   - UUID : stockes en CHAR(36) pour la lisibilite
--   - FK : ON DELETE RESTRICT (protection integrite)
--   - CHECK : omises volontairement sur les colonnes destinees
--     a recevoir des anomalies pedagogiques (progression.pourcentage,
--     temps_connexion.duree_minutes). Documente ici et dans README.
-- =============================================================

-- Selection de la base
USE edusmart_learning;

-- =============================================================
-- Nettoyage : suppression des tables si elles existent deja
-- (ordre inverse des dependances pour respecter les FK)
-- =============================================================

DROP TABLE IF EXISTS temps_connexion;
DROP TABLE IF EXISTS progression;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS quiz;
DROP TABLE IF EXISTS cours;
DROP TABLE IF EXISTS modules;

-- =============================================================
-- Table : modules (bloc Catalogue)
-- Description : brique de plus haut niveau du catalogue pedagogique.
--   Un module regroupe plusieurs cours.
-- =============================================================

CREATE TABLE modules (
    id_module      CHAR(36)      NOT NULL,
    code_module    VARCHAR(20)   NOT NULL,
    nom_module     VARCHAR(150)  NOT NULL,
    categorie      VARCHAR(100)  NOT NULL,
    niveau         VARCHAR(30)   NOT NULL,
    duree_heures   INT           NOT NULL,
    actif          BOOLEAN       NOT NULL DEFAULT TRUE,

    PRIMARY KEY (id_module),
    UNIQUE KEY uq_modules_code (code_module),

    CONSTRAINT chk_modules_duree_positive CHECK (duree_heures > 0)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Modules pedagogiques - brique haute du catalogue';

-- =============================================================
-- Table : cours (bloc Catalogue)
-- Description : lecons appartenant a un module. Un cours n'appartient
--   qu'a un seul module (relation n:1 vers modules).
-- =============================================================

CREATE TABLE cours (
    id_cours       CHAR(36)      NOT NULL,
    id_module      CHAR(36)      NOT NULL,
    titre          VARCHAR(200)  NOT NULL,
    ordre          INT           NOT NULL,
    duree_minutes  INT           NOT NULL,
    type_cours     VARCHAR(30)   NOT NULL,
    statut         VARCHAR(20)   NOT NULL DEFAULT 'PUBLIE',

    PRIMARY KEY (id_cours),

    CONSTRAINT fk_cours_module
        FOREIGN KEY (id_module) REFERENCES modules(id_module)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT chk_cours_ordre_positif    CHECK (ordre > 0),
    CONSTRAINT chk_cours_duree_positive   CHECK (duree_minutes > 0)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Cours appartenant a un module';

-- =============================================================
-- Table : quiz (bloc Catalogue)
-- Description : quiz associes a un cours. Un cours peut avoir zero,
--   un ou plusieurs quiz.
-- =============================================================

CREATE TABLE quiz (
    id_quiz         CHAR(36)      NOT NULL,
    id_cours        CHAR(36)      NOT NULL,
    titre           VARCHAR(150)  NOT NULL,
    nb_questions    INT           NOT NULL,
    score_max       DECIMAL(5,2)  NOT NULL,
    duree_minutes   INT           NOT NULL,

    PRIMARY KEY (id_quiz),

    CONSTRAINT fk_quiz_cours
        FOREIGN KEY (id_cours) REFERENCES cours(id_cours)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT chk_quiz_nb_questions_positif CHECK (nb_questions > 0),
    CONSTRAINT chk_quiz_score_max_positif    CHECK (score_max > 0),
    CONSTRAINT chk_quiz_duree_positive       CHECK (duree_minutes > 0)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Quiz associes a un cours';

-- =============================================================
-- Table : notes (bloc Activite)
-- Description : chaque ligne represente UNE TENTATIVE d'un etudiant
--   a un quiz donne. Un etudiant peut passer plusieurs fois le meme
--   quiz (champ tentative).
--
-- Note importante : student_code est un identifiant fonctionnel
--   partage avec PostgreSQL (format 'LMS-XXXXXX'). PAS de FK vers
--   PostgreSQL : l'integrite referentielle sera verifiee en Phase B
--   (ETL). Anomalie volontaire : quelques student_code fantomes.
-- =============================================================

CREATE TABLE notes (
    id_note        CHAR(36)      NOT NULL,
    id_quiz        CHAR(36)      NOT NULL,
    student_code   VARCHAR(30)   NOT NULL,
    date_passage   DATETIME      NOT NULL,
    score          DECIMAL(5,2)  NOT NULL,
    tentative      INT           NOT NULL DEFAULT 1,
    valide         BOOLEAN       NOT NULL DEFAULT FALSE,

    PRIMARY KEY (id_note),

    CONSTRAINT fk_notes_quiz
        FOREIGN KEY (id_quiz) REFERENCES quiz(id_quiz)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    CONSTRAINT chk_notes_score_positif   CHECK (score >= 0),
    CONSTRAINT chk_notes_tentative_positive CHECK (tentative > 0),

    INDEX idx_notes_student_code (student_code),
    INDEX idx_notes_date_passage (date_passage)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Tentatives de quiz par les etudiants (identifies par student_code)';

-- =============================================================
-- Table : progression (bloc Activite)
-- Description : etat (snapshot) de l'avancement d'un etudiant dans
--   un module. Une seule ligne par couple (etudiant, module).
--   Contrairement a 'notes' qui est evenementielle, cette table est
--   mise a jour (pas ajoutee) a chaque progression.
--
-- Note importante :
--   - Pas de CHECK sur pourcentage : anomalies volontaires (valeurs
--     > 100 et < 0) prevues au catalogue.
--   - dernier_cours est un UUID sans FK : anomalies possibles
--     (references vers cours inexistant).
-- =============================================================

CREATE TABLE progression (
    id_progression   CHAR(36)      NOT NULL,
    student_code     VARCHAR(30)   NOT NULL,
    id_module        CHAR(36)      NOT NULL,
    pourcentage      DECIMAL(5,2)  NOT NULL,
    dernier_cours    CHAR(36)      NULL,
    date_maj         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id_progression),

    CONSTRAINT fk_progression_module
        FOREIGN KEY (id_module) REFERENCES modules(id_module)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    UNIQUE KEY uq_progression_student_module (student_code, id_module),

    INDEX idx_progression_student_code (student_code)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Progression (snapshot) par etudiant et par module';

-- =============================================================
-- Table : temps_connexion (bloc Activite)
-- Description : historique brut des sessions de connexion des
--   etudiants sur la plateforme. Table evenementielle : une ligne
--   par session ouverte.
--
-- Notes importantes :
--   - date_deconnexion nullable : session non fermee proprement
--     (anomalie A12 attendue).
--   - Pas de CHECK sur duree_minutes : anomalies volontaires
--     (durees negatives, anomalie A13).
--   - Pas de FK sur student_code : integrite verifiee en Phase B.
-- =============================================================

CREATE TABLE temps_connexion (
    id_connexion       CHAR(36)      NOT NULL,
    student_code       VARCHAR(30)   NOT NULL,
    date_connexion     DATETIME      NOT NULL,
    date_deconnexion   DATETIME      NULL,
    duree_minutes      INT           NULL,
    appareil           VARCHAR(50)   NULL,
    navigateur         VARCHAR(50)   NULL,
    adresse_ip         VARCHAR(45)   NULL,

    PRIMARY KEY (id_connexion),

    INDEX idx_temps_connexion_student_code (student_code),
    INDEX idx_temps_connexion_date (date_connexion)
)
ENGINE = InnoDB
DEFAULT CHARSET = utf8mb4
COLLATE = utf8mb4_unicode_ci
COMMENT = 'Historique des sessions de connexion des etudiants';