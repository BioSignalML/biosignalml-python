--
-- PostgreSQL database dump
--

-- Started on 2010-11-22 11:58:19 NZDT

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 1804 (class 1262 OID 88939)
-- Name: BioSignalML; Type: DATABASE; Schema: -; Owner: biosignal
--


SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 320 (class 2612 OID 16386)
-- Name: plpgsql; Type: PROCEDURAL LANGUAGE; Schema: -; Owner: postgres
--


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 1510 (class 1259 OID 88959)
-- Dependencies: 6
-- Name: bnodes; Type: TABLE; Schema: public; Owner: biosignal; Tablespace: 
--

CREATE TABLE bnodes (
    id numeric(20,0) NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.bnodes OWNER TO biosignal;

--
-- TOC entry 1508 (class 1259 OID 88943)
-- Dependencies: 6
-- Name: literals; Type: TABLE; Schema: public; Owner: biosignal; Tablespace: 
--

CREATE TABLE literals (
    id numeric(20,0) NOT NULL,
    value text NOT NULL,
    language text NOT NULL,
    datatype text NOT NULL
);


ALTER TABLE public.literals OWNER TO biosignal;

--
-- TOC entry 1511 (class 1259 OID 88967)
-- Dependencies: 6
-- Name: models; Type: TABLE; Schema: public; Owner: biosignal; Tablespace: 
--

CREATE TABLE models (
    id numeric(20,0) NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.models OWNER TO biosignal;

--
-- TOC entry 1509 (class 1259 OID 88951)
-- Dependencies: 6
-- Name: resources; Type: TABLE; Schema: public; Owner: biosignal; Tablespace: 
--

CREATE TABLE resources (
    id numeric(20,0) NOT NULL,
    uri text NOT NULL
);


ALTER TABLE public.resources OWNER TO biosignal;


CREATE SEQUENCE users_rowid
    START WITH 2
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.users_rowid OWNER TO biosignal;

--
-- TOC entry 1512 (class 1259 OID 88979)
-- Dependencies: 1791 6
-- Name: users; Type: TABLE; Schema: public; Owner: biosignal; Tablespace: 
--

CREATE TABLE users (
    username text NOT NULL,
    password text,
    changepw integer,
    level integer,
    rowid bigint DEFAULT nextval('users_rowid'::regclass) NOT NULL
);


ALTER TABLE public.users OWNER TO biosignal;

--
-- TOC entry 1797 (class 2606 OID 88966)
-- Dependencies: 1510 1510
-- Name: bnodes_pkey; Type: CONSTRAINT; Schema: public; Owner: biosignal; Tablespace: 
--

ALTER TABLE ONLY bnodes
    ADD CONSTRAINT bnodes_pkey PRIMARY KEY (id);


--
-- TOC entry 1793 (class 2606 OID 88950)
-- Dependencies: 1508 1508
-- Name: literals_pkey; Type: CONSTRAINT; Schema: public; Owner: biosignal; Tablespace: 
--

ALTER TABLE ONLY literals
    ADD CONSTRAINT literals_pkey PRIMARY KEY (id);


--
-- TOC entry 1799 (class 2606 OID 88974)
-- Dependencies: 1511 1511
-- Name: models_pkey; Type: CONSTRAINT; Schema: public; Owner: biosignal; Tablespace: 
--

ALTER TABLE ONLY models
    ADD CONSTRAINT models_pkey PRIMARY KEY (id);


--
-- TOC entry 1795 (class 2606 OID 88958)
-- Dependencies: 1509 1509
-- Name: resources_pkey; Type: CONSTRAINT; Schema: public; Owner: biosignal; Tablespace: 
--

ALTER TABLE ONLY resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (id);



INSERT INTO users (username, password, changepw, level, rowid)
 values ( 'admin', 'admin', 0, 9, 1) ;


--
-- TOC entry 1801 (class 2606 OID 88986)
-- Dependencies: 1512 1512
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: biosignal; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (username);


--
-- TOC entry 1806 (class 0 OID 0)
-- Dependencies: 6
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2010-11-22 11:58:20 NZDT

--
-- PostgreSQL database dump complete
--

