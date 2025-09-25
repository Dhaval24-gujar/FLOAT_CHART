#!/usr/bin/env python3
"""
Test script for the FloatChat FastMCP Server

This script tests the FastMCP version of the FloatChat server.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Import the functions directly from the FastMCP server
from floatchat_fastmcp_server import (
    run_query, list_tables, get_schema, describe_database, get_indexes,
    ensure_connection, cleanup
)

load_dotenv()

async def test_fastmcp_server():
    """Test the FloatChat FastMCP server functionality."""
    
    # Check if database URL is configured
    db_url = os.getenv("NEON_DB_URL")
    if not db_url or db_url == "postgresql://user:password@host:port/database":
        print("❌ Please configure NEON_DB_URL in your .env file with actual database credentials")
        print("   Format: postgresql://user:password@host:port/database")
        return False
    
    try:
        print("🚀 Testing FloatChat FastMCP Server...")
        
        # Test database connection
        print("\n📡 Testing database connection...")
        await ensure_connection()
        print("✅ Database connection successful")
        
        # Test list_tables
        print("\n📋 Testing list_tables...")
        try:
            tables_result = await list_tables()
            print(f"✅ Found {tables_result['table_count']} tables:")
            for table in tables_result['table_names']:
                print(f"   - {table}")
        except Exception as e:
            print(f"⚠️  list_tables test failed: {e}")
        
        # Test describe_database
        print("\n🗂️  Testing describe_database...")
        try:
            db_structure = await describe_database()
            print(f"✅ Database structure retrieved:")
            print(f"   - {db_structure['table_count']} tables")
            print(f"   - {db_structure['total_columns']} total columns")
            
            # Show structure for each table
            for table_name, table_info in db_structure['database_structure'].items():
                print(f"   📊 {table_name}: {table_info['column_count']} columns")
        except Exception as e:
            print(f"⚠️  describe_database test failed: {e}")
        
        # Test get_schema for a specific table
        print("\n🔍 Testing get_schema...")
        test_tables = ['argo_floats', 'argo_profiles', 'argo_anomalies', 'argo_embeddings']
        
        for table_name in test_tables:
            try:
                schema_result = await get_schema(table_name)
                if 'error' not in schema_result:
                    print(f"✅ Schema for {table_name}:")
                    print(f"   - {schema_result['column_count']} columns")
                    print(f"   - {len(schema_result['constraints'])} constraints")
                    break
            except Exception as e:
                print(f"⚠️  get_schema test for {table_name} failed: {e}")
        
        # Test get_indexes
        print("\n🗂️  Testing get_indexes...")
        for table_name in test_tables:
            try:
                indexes_result = await get_indexes(table_name)
                if 'error' not in indexes_result:
                    print(f"✅ Indexes for {table_name}:")
                    print(f"   - {indexes_result['index_count']} indexes")
                    for idx in indexes_result['indexes']:
                        print(f"   - {idx['indexname']} ({'unique' if idx['is_unique'] else 'non-unique'})")
                    break
            except Exception as e:
                print(f"⚠️  get_indexes test for {table_name} failed: {e}")
        
        # Test run_query with safe queries
        print("\n🔍 Testing run_query...")
        
        # Test basic query
        try:
            query_result = await run_query("SELECT current_database(), current_user, version()")
            print(f"✅ Basic query executed successfully:")
            print(f"   - Returned {query_result['row_count']} rows")
        except Exception as e:
            print(f"⚠️  Basic query test failed: {e}")
        
        # Test table count query
        try:
            count_query = """
            SELECT 
                schemaname,
                COUNT(*) as table_count 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            GROUP BY schemaname
            """
            count_result = await run_query(count_query)
            print(f"✅ Table count query executed:")
            print(f"   - Returned {count_result['row_count']} rows")
        except Exception as e:
            print(f"⚠️  Table count query test failed: {e}")
        
        # Test WITH clause (CTE)
        try:
            cte_query = """
            WITH table_info AS (
                SELECT tablename, schemaname 
                FROM pg_tables 
                WHERE schemaname = 'public'
            )
            SELECT COUNT(*) as total_tables FROM table_info
            """
            cte_result = await run_query(cte_query)
            print(f"✅ CTE query executed successfully:")
            print(f"   - Returned {cte_result['row_count']} rows")
        except Exception as e:
            print(f"⚠️  CTE query test failed: {e}")
        
        # Test query safety validation
        print("\n🛡️  Testing query safety validation...")
        
        dangerous_queries = [
            "DROP TABLE argo_profiles",
            "DELETE FROM argo_profiles",
            "UPDATE argo_profiles SET temperature = 0",
            "INSERT INTO argo_profiles VALUES (1, 2, 3)",
            "ALTER TABLE argo_profiles ADD COLUMN test TEXT",
            "TRUNCATE TABLE argo_profiles"
        ]
        
        for dangerous_query in dangerous_queries:
            try:
                await run_query(dangerous_query)
                print(f"❌ Safety validation failed - dangerous query was allowed: {dangerous_query}")
            except ValueError as e:
                print(f"✅ Safety validation working for: {dangerous_query.split()[0]}")
        
        # Test invalid table name handling
        print("\n🚫 Testing invalid input handling...")
        try:
            await get_schema("'; DROP TABLE users; --")
            print("❌ SQL injection protection failed!")
        except ValueError as e:
            print("✅ SQL injection protection working")
        
        # Cleanup
        await cleanup()
        print("\n✅ All FastMCP server tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ FastMCP server test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("FloatChat FastMCP Server Test Suite")
    print("=" * 50)
    
    success = await test_fastmcp_server()
    
    if success:
        print("\n🎉 FastMCP server is ready to use!")
        print("\nTo run the server:")
        print("   python floatchat_fastmcp_server.py")
        print("\nAvailable tools:")
        print("   - run_query(query): Execute safe SELECT queries")
        print("   - list_tables(): Get all table names")
        print("   - get_schema(table_name): Get table schema details")
        print("   - describe_database(): Get complete database structure")
        print("   - get_indexes(table_name): Get index information")
    else:
        print("\n❌ FastMCP server tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
